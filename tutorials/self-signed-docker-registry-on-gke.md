---
title: Using a self-signed Docker Registry on GKE
description: Using a self-signed Docker Registry on GKE
author: samos123
tags: Kubernetes Engine, GKE, Docker Registry
date_published: 2020-01-28
---

This tutorial shows how to use a Docker registry that was signed by a 
non-trusted CA with Google Kubernetes Engine (GKE). Let's assume your company
has a private CA that's not trusted by default.
All internal services such as on-prem docker registry have their certs signed
by this private CA. This would cause GKE to prevent pulling from the on-prem
registry since it's not trusted. In this guide we assume the private CA cert is
stored in a file called `myCA.pem`.

The solution is to import the CA into the system bundle and restart docker.
However on GKE, COS is used which makes this harder. The following steps
are needed on GKE:
1. Create a docker image that that has `myCA.pem`, copies the `myCA.pem` 
   into `/mnt/etc/ssl/certs/`, runs `update-ca-certificates` and restart
   docker daemon.
2. Create a daemonset that runs this docker image on every node and mount
   the host `/etc` directory to the containers `/mnt/etc` directory

## Before you begin
You will need the following resources:
* A Docker registry that was signed by an untrusted CA
* GKE cluster that has access to the self-signed registry
* kubectl configured to use the GKE cluster

## 1. Creating the CA inserter docker image

Create the Dockerfile for our image that will insert the CA:
```
mkdir custom-cert
cd custom-cert
cat > Dockerfile <<EOF
FROM ubuntu
COPY myCA.pem /myCA.pem
COPY insert-ca.sh /usr/sbin/
CMD insert-ca.sh
EOF
```

This is the script `insert-ca.sh` that will be used in the Docker image:
```bash
cat > insert-ca.sh <<EOF
#!/bin/bash

cp /myCA.pem /mnt/etc/ssl/certs
nsenter --target 1 --mount update-ca-certificates
nsenter --target 1 --mount systemctl restart docker
EOF
chmod +x insert-ca.sh
```
Now build and push the image to GCR:
```
# Set project ID to current project or desired project
PROJECT_ID="$(gcloud config get-value project -q)"
docker build -t gcr.io/$PROJECT_ID/custom-cert .
docker push gcr.io/$PROJECT_ID/custom-cert
```

## 2. Deploy daemonset to insert CA on GKE nodes
Now that we've the insert CA docker image built we can run it on each node
using a DaemonSet. This will ensure that we add more nodes that the same
customization is applied as well. The daemonset uses privileged mode to
get access to the GKE node. It also mounts the GKE node `/etc` directory
to the containers `/mnt/etc` directory.

Use the following DaemonSet to run the insert CA container on all nodes:
```
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cert-customizations
  labels:
    app: cert-customizations
spec:
  selector:
    matchLabels:
      app: cert-customizations
  template:
    metadata:
      labels:
        app: cert-customizations
    spec:
      hostNetwork: true
      hostPID: true
      initContainers:
      - name: cert-customizations
        image: gcr.io/$PROJECT_ID/custom-cert
        volumeMounts:
          - name: etc
            mountPath: "/mnt/etc"
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
      volumes:
      - name: etc
        hostPath:
          path: /etc
      containers:
      - name: pause
        image: gcr.io/google_containers/pause
EOF
```

After the DaemonSet has been run you will notice that you can pull from a self-signed
registry in GKE. You can validate this by creating a pod where the image source
is the self-signed registry.
