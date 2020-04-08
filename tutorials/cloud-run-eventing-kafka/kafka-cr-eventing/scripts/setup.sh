#!/usr/bin/env bash

#### This Script is meant to setup a functioning Cloud Run on Anthos Cluster for testing. 


#### logging 
exec > >(tee -i logfile.txt)


#### Declare MYROOT directory for cloned repo
export MYROOT=$(pwd)
clear 
### install golang v1.13.1

mkdir ~/.golang
cd ~/.golang
if ! [ -x "$(command -v go)" ]; then
    echo "***** Installing GoLang v1.13.1 *****"
    if [[ "$OSTYPE"  == "linux-gnu" ]]; then
        curl https://dl.google.com/go/go1.13.1.linux-amd64.tar.gz -o go1.13.1.linux-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.13.1.linux-amd64.tar.gz
        echo "export PATH=$PATH:/usr/local/go/bin" >> ~/.profile
        #source ~/.profile
        export PATH=$PATH:/usr/local/go/bin

    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl https://dl.google.com/go/go1.13.1.darwin-amd64.tar.gz -o go1.13.1.darwin-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.13.1.darwin-amd64.tar.gz
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

#### Installing Confluent Cloud SDK
if ! [ -x "$(command -v ccloud)" ]; then
    echo "***** Installing Confluent Cloud CLI *****"
    curl -L https://cnfl.io/ccloud-cli | sudo sh -s -- -b /usr/local/bin
else 
    echo "Confluent Cloud CLI is already installed. Let's move on"
fi   

echo "***** Log into Confluent Cloud *****"
ccloud login --url https://confluent.cloud

echo "***** Create a Kafka Cluster called 'cloudrun' *****"
export CONFLUENT_ID=$(ccloud kafka cluster create cloudrun --cloud gcp --region us-central1 | grep 'Id' | sed 's/^.* | //' | cut -f3-4 -d"/" | tr -d '|')
export CONFLUENT_ENV=$(ccloud environment list | grep "*" | cut -c4-9)
ccloud environment use $CONFLUENT_ENV
ccloud kafka cluster use $CONFLUENT_ID
ccloud kafka cluster list
sleep 60

#### Get Confluent 
export CONFLUENT_HOST=$(ccloud kafka cluster describe `ccloud kafka cluster list | grep "*" | cut -c4-14` | grep 'SASL_SSL'  | sed 's/^.* | //' | cut -f3-4 -d"/" | tr -d '|')
#### Setting API Keys for Confluent
ccloud api-key create > secrets.txt
export CONFLUENT_KEY=$(grep 'API Key |' secrets.txt | sed 's/^.* | //' | cut -d' ' -f1)
export CONFLUENT_SECRET=$(grep 'Secret  |' secrets.txt | sed 's/^.* | //' | cut -d' ' -f1)
rm -rf secrets.txt
clear

ccloud api-key use $CONFLUENT_KEY


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
  --machine-type=n1-standard-2 \
  --cluster-version=latest \
  --zone=$ZONE \
  --enable-stackdriver-kubernetes \
  --scopes cloud-platform

#wait for 90 seconds
echo "***** Waiting for 90 second for cluster to complete *****"
sleep 90

echo "***** Create a Kafka Topic called 'cloudevents' *****"
ccloud kafka topic create cloudevents

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
export EXTERNAL_IP=$(kubectl get service istio-ingressgateway --namespace istio-system | awk 'FNR == 2 {print $4}')

echo "***** We will now patch configmap for domain ******"
kubectl patch configmap config-domain --namespace knative-serving --patch \
'{"data": {"example.com": null, "'"$EXTERNAL_IP"'.xip.io": ""}}'

#### Install Knative Eventing
clear
echo "***** Installing Knative Eventing ******"

kubectl apply --selector knative.dev/crd-install=true \
--filename https://github.com/knative/eventing/releases/download/v0.10.0/release.yaml \
--filename https://github.com/knative/serving/releases/download/v0.10.0/monitoring.yaml

kubectl apply --filename https://github.com/knative/eventing/releases/download/v0.10.0/release.yaml \
--filename https://github.com/knative/serving/releases/download/v0.10.0/monitoring.yaml

#ElasticSearch Monitoring
kubectl apply --filename https://github.com/knative/serving/releases/download/v0.10.0/monitoring-logs-elasticsearch.yaml

kubectl get pods --namespace knative-eventing
kubectl get pods --namespace knative-monitoring

# Setup namespace
kubectl create namespace kafka-eventing

kubectl label namespace kafka-eventing knative-eventing-injection=enabled



#### Prepaing YAML
clear
echo "***** Let's deploy Knative Eventing for Kafka *****"
cd $MYROOT && cd config/kafka
kubectl apply -f kafka-source-release-0.10.yaml
sed 's|KAFKA-KEY|'"$CONFLUENT_KEY"'|g; s|KAFKA-SECRET|'"$CONFLUENT_SECRET"'|g' kafka-secrets.sample.yaml > kafka-secrets.yaml
kubectl apply -f kafka-secrets.yaml
sed 's|CONFLUENT-SERVER|'"$CONFLUENT_HOST"'|g' kafka-source-deploy.sample.yaml > kafka-source-deploy.yaml
kubectl apply -f kafka-source-deploy.yaml
sed 's|CONFLUENT-SERVER|'"$CONFLUENT_HOST"'|g' kafka-source-display.sample.yaml > kafka-source-display.yaml
kubectl apply -f kafka-source-display.yaml
clear
echo "***** DEPLOYED! *****"
kubectl label namespace default knative-eventing-injection=enabled


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