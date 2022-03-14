#!/bin/sh
#

sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update && sudo apt-get install -y docker-ce
sudo groupadd docker
sudo usermod -a -G docker $USER
sudo systemctl enable docker
sudo curl -L https://github.com/docker/compose/releases/download/1.18.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -a -G docker $USER
git clone https://github.com/Kcr19/integration.git mender-server
cd mender-server
git checkout -b my-production-setup
cp -a template production
cd production
wget -O prod.yml https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-iot-mender-ota/server/prod.yml
sed -i -e 's#/template/#/production/#g' prod.yml
git config --global user.email "test@example.com"
git config --global user.name test.mender "Test"
git add .
git commit -m 'production: initial template'
./run pull
CERT_API_CN=mender.gcpotademo.com CERT_STORAGE_CN=gcs.mender.gcpotademo.com ../keygen
git add keys-generated
git commit -m 'production: adding generated keys and certificates'
docker volume create --name=mender-artifacts
docker volume create --name=mender-deployments-db
docker volume create --name=mender-useradm-db
docker volume create --name=mender-inventory-db
docker volume create --name=mender-deviceadm-db
docker volume create --name=mender-deviceauth-db
docker volume create --name=mender-elasticsearch-db
docker volume create --name=mender-redis-db
docker volume inspect --format '{{.Mountpoint}}' mender-artifacts
git add prod.yml
git commit -m 'production: final configuration'
./run up -d
sudo ./run exec -T mender-useradm /usr/bin/useradm create-user --username=mender@example.com --password=mender_gcp_ota
export FULL_PROJECT=$(gcloud config list project --format "value(core.project)")
export PROJECT="$(echo $FULL_PROJECT | cut -f2 -d ':')"
export REGION='us-central1'
gsutil cp keys-generated/certs/server.crt gs://$PROJECT-mender-server/certs/
