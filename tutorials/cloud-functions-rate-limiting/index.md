
# Bare tutorial steps
see go/rate-limiting-patterns for internal draft

in cloud shell:

```
git clone https://github.com/ptone/community.git
cd community
git checkout rate-limiting
cd tutorials/cloud-functions-rate-limiting
```

## Setup Env

```
# this is automatic in Cloud Shell
gcloud config set project [ your project id ]

export REGION=us-central1
export GOOGLE_CLOUD_PROJECT=$(gcloud config list project --format "value(core.project)" )

export NETWORK=rate-limiting-demo


gcloud services enable \
cloudfunctions.googleapis.com \
compute.googleapis.com \
redis.googleapis.com \
servicenetworking.googleapis.com \
vpcaccess.googleapis.com
```

```
gcloud compute networks create $NETWORK 
gcloud compute networks subnets update ${NETWORK} --region ${REGION} --enable-private-ip-google-access
https://cloud.google.com/functions/docs/connecting-vpc
gcloud beta compute networks vpc-access connectors create functions-connector \
--network ${NETWORK} \
--region ${REGION} \
--range 10.8.0.0/28
```

Note - set by default on container VMs:
Registry Mirrors:
 https://mirror.gcr.io/

```
gcloud beta compute instances create-with-container redis \
--zone=${REGION}-a \
--machine-type=g1-small \
--no-address \
--container-image=redis \
--container-restart-policy=always \
--subnet=${NETWORK} \
--scopes=https://www.googleapis.com/auth/devstorage.read_only
```

```
export REDIS_HOST=$(gcloud compute instances describe redis --format='value(networkInterfaces[0].networkIP)' --zone=${REGION}-a)

# cd basic-rate
gcloud beta functions deploy basicRateDemo --runtime nodejs10 --trigger-http --source ./build  --set-env-vars=REDIS_HOST=${REDIS_HOST} --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector --region ${REGION}
```

`go get -u github.com/codesenberg/bombardier`


get URL of func

`bombardier -r 12 -d 5s https://us-central1-ptone-kf.cloudfunctions.net/basicRateDemo`

## IP Rate Demo

# cp the package.json file in

gcloud beta functions deploy IPRateDemo --runtime nodejs10 --trigger-http --source ./build  --set-env-vars=REDIS_HOST=${REDIS_HOST} --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector --region ${REGION}

bombardier -r 8 -d 30s https://us-central1-ptone-kf.cloudfunctions.net/IPRateDemo

bombardier -r 500 -d 10s https://us-central1-ptone-kf.cloudfunctions.net/IPRateDemo

## Firestore Counter
gcloud beta functions deploy counterLimit --runtime nodejs10 --trigger-http --source ./build  --set-env-vars=REDIS_HOST=${REDIS_HOST} --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector --region ${REGION}


## User based example...

## Cleanup

gcloud functions delete basicRateDemo --quiet && \
gcloud functions delete IPRateDemo --quiet && \
gcloud beta compute instances delete redis --zone=${REGION}-a --quiet && \
gcloud beta compute networks vpc-access connectors create functions-connector --quiet && \
gcloud compute networks delete $NETWORK --quiet



# appendix
gcloud beta redis instances create mredis --size=1 --region=us-central1 --redis-version=redis_4_0 --project ptone-anthos

gcloud compute instances create --zone us-central1-a \
--subnet=${NETWORK} \
util
--project ptone-anthos util


gcloud beta compute instances create-with-container redis-pub --zone=us-central1-c --machine-type=g1-small  --image=cos-stable-74-11895-86-0 --image-project=cos-cloud --container-image=us.gcr.io/cloud-solutions-images/redis --container-restart-policy=always  --scopes=https://www.googleapis.com/auth/devstorage.read_only


gcloud beta functions deploy basicRateDemoC --runtime nodejs10 --trigger-http --source ./build  --set-env-vars=REDIS_HOST=${REDISP}

go get -u github.com/codesenberg/bombardier




https://bit.googleplex.com/#/ptone/5907504743579648