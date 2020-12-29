#!/usr/bin/env bash

#### This Script is meant to setup a functioning Cloud Run on Anthos Cluster for testing. 


#### logging 
exec > >(tee -i logfile.txt)


#### Declare MYROOT directory for cloned repo
export MYROOT=$(pwd)
clear 
### install golang v1.14

mkdir ~/.golang
cd ~/.golang
if ! [ -x "$(command -v go)" ]; then
    echo "***** Installing GoLang v1.14 *****"
    if [[ "$OSTYPE"  == "linux-gnu" ]]; then
        curl https://dl.google.com/go/go1.14.linux-amd64.tar.gz -o go1.14.linux-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.14.linux-amd64.tar.gz
        echo "export PATH=$PATH:/usr/local/go/bin" >> ~/.profile
        #source ~/.profile
        export PATH=$PATH:/usr/local/go/bin

    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl https://dl.google.com/go/go1.14.darwin-amd64.tar.gz -o go1.14.darwin-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.14.darwin-amd64.tar.gz
        echo "export PATH=$PATH:/usr/local/go/bin" >> ~/.bash_profile
        #source ~/.bash_profile
        export PATH=$PATH:/usr/local/go/bin
    else
        echo "unknown OS"
    fi
else 
    echo "GoLang is already installed. Let's move on"
fi


#cleanup .golang
cd $MYROOT
rm -rf .golang

clear

### install Google Cloud SDK
if ! [ -x "$(command -v gcloud)" ]; then
    echo "***** Installing Google Cloud SDK *****"
    if [[ "$OSTYPE"  == "linux-gnu" ]]; then
        curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-266.0.0-linux-x86_64.tar.gz -o google-cloud-sdk-266.0.0-linux-x86_64.tar.gz
        tar xf google-cloud-sdk-266.0.0-linux-x86_64.tar.gz && ./google-cloud-sdk/install.sh
        echo "export PATH=$PATH:/usr/local/go/bin" >> ~/.profile
        #source ~/.profile
        export PATH=$PATH:/usr/local/go/bin
        gcloud auth login

    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-266.0.0-darwin-x86_64.tar.gz -o google-cloud-sdk-266.0.0-darwin-x86_64.tar.gz
        tar xf google-cloud-sdk-266.0.0-darwin-x86_64.tar.gz && ./google-cloud-sdk/install.sh
        echo "export PATH=$PATH:/usr/local/go/bin" >> ~/.bash_profile
        #source ~/.bash_profile
        export PATH=$PATH:/usr/local/go/bin
        gcloud auth login
    else
        echo "unknown OS"
    fi
    gcloud init
    exit 1
else 
    echo "Google Cloud SDK is already installed. Let's move on"
fi



#### BoilerPlate Code for
cd $MYROOT

clear
echo "******Setting Variables******"

export ZONE='us-central1-a'
export PROJECT_ID=$(gcloud config get-value project)
export PROJ_NUMBER=$(gcloud projects list --filter="${PROJECT_ID}" --format="value(PROJECT_NUMBER)")
export BUCKET_ID='my-secrets'

### Setup Basic Environment
clear
echo "***** Setting Project and Zone *****"
gcloud config set project $PROJECT_ID
gcloud config set compute/zone $ZONE

echo "***** Making sure you have APIs ready to go *****"
gcloud services enable container.googleapis.com \
containerregistry.googleapis.com \
cloudbuild.googleapis.com \
cloudkms.googleapis.com \
storage-api.googleapis.com \
storage-component.googleapis.com \
cloudscheduler.googleapis.com


echo "****** We will make sure the Google Cloud SDK is running beta components and kubectl ******"
gcloud components update
gcloud components install beta
gcloud components install kubectl

### Creating Cluster
clear
echo "******Now we shall create your cluster******"
gcloud beta container clusters create $CLUSTER_NAME \
  --addons=HorizontalPodAutoscaling,HttpLoadBalancing,Istio,CloudRun \
  --machine-type=n1-standard-4 \
  --cluster-version=latest \
  --zone=$ZONE \
  --enable-stackdriver-kubernetes \
  --scopes cloud-platform

#wait for 90 seconds
echo "***** Waiting for 90 second for cluster to complete *****"
sleep 90


### Configuring your cluster for Run
echo "******Now we ensure that your cluster has Cloud Run******"
gcloud config set run/platform gke
gcloud config set run/cluster $CLUSTER_NAME
gcloud config set run/cluster_location $ZONE
gcloud container clusters get-credentials $CLUSTER_NAME
kubectl create namespace kafka-eventing
kubectl label namespace default knative-eventing-injection=enabled
kubectl label namespace kafka-eventing knative-eventing-injection=enabled
gcloud config set run/namespace kafka-eventing


##### Get istio-gateway external IP
echo "****** We are going to grab the external IP ******"
export EXTERNAL_IP=$(kubectl get service istio-ingress --namespace gke-system | awk 'FNR == 2 {print $4}')

echo "***** We will now patch configmap for domain ******"
kubectl patch configmap config-domain --namespace knative-serving --patch \
'{"data": {"example.com": null, "'"$EXTERNAL_IP"'.xip.io": ""}}'

#### Install Knative Eventing
clear
echo "***** Installing Knative Eventing ******"

kubectl apply --selector knative.dev/crd-install=true \
--filename https://github.com/knative/eventing/releases/download/v0.11.0/eventing.yaml \
--filename https://github.com/knative/serving/releases/download/v0.11.0/monitoring.yaml

kubectl apply --filename https://github.com/knative/eventing/releases/download/v0.11.0/eventing.yaml \
--filename https://github.com/knative/serving/releases/download/v0.11.0/monitoring.yaml



kubectl apply --selector knative.dev/crd-install=true \
--filename https://github.com/knative/eventing/releases/download/v0.12.0/eventing.yaml \
--filename https://github.com/knative/serving/releases/download/v0.12.0/monitoring.yaml


kubectl apply --filename https://github.com/knative/eventing/releases/download/v0.12.0/eventing.yaml \
--filename https://github.com/knative/serving/releases/download/v0.12.0/monitoring.yaml


#ElasticSearch Monitoring
#kubectl apply --filename https://github.com/knative/serving/releases/download/v0.10.0/monitoring-logs-elasticsearch.yaml

kubectl get pods --namespace knative-eventing
kubectl get pods --namespace knative-monitoring


# Permissions
echo "Setting up cluster permissions"
kubectl create clusterrolebinding cluster-admin-binding \
--clusterrole=cluster-admin \
--user=$(gcloud config get-value core/account)



#### app
clear
cd $MYROOT && cd apps/currency
echo "***** Building Container *****"
gcloud builds submit --tag gcr.io/$PROJECT_ID/currency-app . 
echo ''
echo "***** CCONTAINER BUILT! *****"

### And Now we Deploy the new one
clear
echo "****** Lets deploy our Currency App ******"

gcloud beta run deploy currency-app --image gcr.io/$PROJECT_ID/currency-app \
--platform gke --cluster $CLUSTER_NAME --cluster-location $ZONE \
--connectivity=external \
--namespace kafka-eventing \
--update-env-vars CONFLUENT_KEY=$CONFLUENT_KEY,CONFLUENT_SECRET=$CONFLUENT_SECRET,ALPHAVANTAGE_KEY=$AV_KEY,CONFLUENT_HOST=$CONFLUENT_HOST



### Cloud Scheduler Time

gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$PROJ_NUMBER-compute@developer.gserviceaccount.com --role roles/cloudscheduler.jobRunner

clear
echo "***** Wait 60 seconds *****"
sleep 60

export SVCURL="$(gcloud beta run services list --format=json| grep "currency-app" | grep "xip.io" | cut -d: -f2- |tr -d '"')/api/v1/currency?currency1=USD&currency2=JPY"

gcloud scheduler jobs create http currency-job --schedule="* * * * *" --uri $SVCURL --http-method POST

###TODO -- Google Cloud Build Tutorial ###
### Setting up Cloud Build
#### https://cloud.google.com/cloud-build/docs/securing-builds/use-encrypted-secrets-credentials

gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$PROJ_NUMBER@cloudbuild.gserviceaccount.com --role roles/container.developer

clear
echo "***** Congrats! You are good to go! *****"