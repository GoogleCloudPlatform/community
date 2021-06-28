#!/bin/sh

# delete the cluster 
gcloud -q container clusters delete $CLUSTER_NAME --zone=$ZONE
# delete the SQL instance
gcloud -q sql instances delete $MYSQL_NAME
# delete the service account
gcloud -q iam service-accounts delete $SQL_SERVICE_ACCOUNT
# delete the disk
gcloud -q compute disks delete nfs-pv-disk --zone=$ZONE
# delete Container Registry images
gcloud -q container images delete gcr.io/$PROJECT_ID/mypresta:1.0.1
