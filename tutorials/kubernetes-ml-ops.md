---
title: Kubernetes ML ops
description: An introduction to machine learning model deployment operations (MLOps) using Python and Kubernetes.
author: Karan
tags: kubernetes-MLOps
date_published: 2020-04-23
---
## Deploying Machine Learning Models on Kubernetes

A common pattern for deploying Machine Learning (ML) models into production environments - e.g. ML models trained using the SciKit Learn or Keras packages (for Python), that are ready to provide predictions on new data - is to expose these ML as RESTful API microservices, hosted from within Docker containers. These can then deployed to a cloud environment for handling everything required for maintaining continuous availability

Kubernetes is a container orchestration platform. Briefly, it provides a mechanism for defining entire microservice-based application deployment topologies and their service-level requirements for maintaining continuous availability.

### Create a GCP project

A default project is often set up by default for new accounts, but you
will start by creating a new project to keep this separate and easy to
tear down later. After creating it, be sure to copy down the `project id` as it
is usually different then the `project name`.

![How to find your project id.][image1]

[image1]: https://storage.googleapis.com/gcp-community/tutorials/getting-started-on-gcp-with-terraform/gcp_project_id.png "Project Id"

### Open Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-console-menu] button in the navigation bar in the upper-right corner of the console.

Now let's created a project directory via console
```
$ mkdir py-flask-ml-rest-api
```

### Containerising a Simple ML Model Scoring Service using Flask and Docker

We start by demonstrating how to achieve this basic competence using the simple Python ML model scoring REST API contained in the api.py module, together with the Dockerfile, both within the py-flask-ml-rest-api directory, whose core contents are as follows,

```
py-flask-ml-rest-api/
 | Dockerfile
 | api.py ## Needs to be alter as per your requirenment and ML model

```
### Defining the Flask Service in the api.py Module

This is a Python module that uses the Flask framework for defining a web service (app), with a function (score), that executes in response to a HTTP request to a specific URL (or 'route')

**api.py**

```python
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)


@app.route('/score', methods=['POST'])
def score():
    features = request.json['X']
    return make_response(jsonify({'score': features}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

```
### Defining the Docker Image with the Dockerfile

**Dockerfile**

```dockerfile
FROM python:3.6-slim
WORKDIR /usr/src/app
COPY . .
RUN pip install flask

EXPOSE 5000
CMD ["python", "api.py"]

```
Let's build the dockerfile from your gcp console

```docker
$ docker build -t ml-k8s .
```

### Pushing the Docker Image to GCR ( Google Cloud Registry )

```docker
$ docker tag ml-k8s [HOSTNAME]/[PROJECT-ID]/ml-k8s
$ docker push [HOSTNAME]/[PROJECT-ID]/ml-k8s
```


> For details regarding GCR, Please have a look - [Google Cloud Registry](https://cloud.google.com/container-registry/docs/quickstart)

> Once your Docker file is build successfully and pushed to GCR, we are done with Containerising ML Model

### Setting up Kubernetes Custer

####  Before you begin

* Ensure that you have enabled the Google Kubernetes Engine API, within the GCP UI visit the Kubernetes Engine page to trigger the Kubernetes API to start-up

From the command line we then start a cluster using
```CLI
$ gcloud container clusters create k8s-ml-cluster --num-nodes 3 --machine-type g1-small --zone us-west1b
```

And then let's wait for the cluster to be created.

For connecting to k8s-ml-cluster

```
$ gcloud container clusters get-credentials tf-gke-k8s --zone us-west1-b --project <PROJECT_ID>
```

> For More details - Please have a look - [Creating a Kubernetes cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-cluster)

### Deploying the Containerised ML Model to Kubernetes

*Project Structure* 

```
| api.py
| base
  | namespace.yaml
  | deployment.yaml
  | service.yaml
  | kustomize.yaml
| Dockerfile

```
Writing YAML files for Kubernetes can get repetitive and hard to manage, espically its painful when there are multiple files and we need to execute them one by one.
So for executing all the kubernetes yaml files will be using Kustomize. ``kustomize`` lets you customize raw, template-free YAML files for multiple purposes, leaving the original YAML untouched and usable as is.

*Steps for Installing Kustomize*

```bash
curl -s https://api.github.com/repos/kubernetes-sigs/kustomize/releases |\
grep browser_download |\
grep linux |\
cut -d '"' -f 4 |\
grep /kustomize/v |\
sort | tail -n 1 |\
xargs curl -O -L && \
tar xzf ./kustomize_v*_linux_amd64.tar.gz && \
mv kustomize /usr/bin/
```

**namespace.yaml**

Namespaces provide a scope for Kubernetes resources, carving up your cluster in smaller units.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mlops
```

**deployment.yaml**

Deployments represent a set of multiple, identical Pods with no unique identities. A Deployment runs multiple replicas of your application and automatically replaces any instances that fail or become unresponsive

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: score-app
    env: qa
  name: score-app
  namespace: mlops
spec:
  replicas: 2 # Creating two PODs for our app
  selector:
    matchLabels:
      app: score-app
  template:
    metadata:
      labels:
        app: score-app
        env: qa
    spec:
      containers:
      - image: <DOCKER_IMAGE_NAME> # Docker image name, that we pushed to GCR
        name: <CONTAINER_NAME>     # POD name 
        ports:
        - containerPort: 5000
          protocol: TCP

```
**service.yaml**

An abstract way to expose an application running on a set of Pods as a network service.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: score-app
  labels:
    app: score-app
  namespace: mlops
spec:
  type: LoadBalancer
  ports:
  - port: 5000
    targetPort: 5000
  selector:
    app: score-app

```
**kustomize.yaml**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- namespace.yaml
- deployment.yaml
- service.yaml

```
After setting this up we can deploy our app using the single command,

```
kubectl apply --kustomize=${PWD}/base/ --record=true
```

To see all components deployed into this namespace use
```
$ kubectl get ns

NAME              STATUS   AGE
default           Active   35m
kube-node-lease   Active   35m
kube-public       Active   35m
kube-system       Active   35m
mlops             Active   33s
staging           Active   34m
```
```
$ kubectl get deployment -n mlops

NAME        READY   UP-TO-DATE   AVAILABLE   AGE
score-app   2/2     2            2           100s
```

```
$ kubectl get service -n mlops

NAME        TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)          AGE
score-app   LoadBalancer   xx.xx.xx.xx   xx.xx.xx.xx   5000:xxxx/TCP   2m3s
```

### Now we test our new deployed model

```bash
curl http://<EXTERNAL-IP>:5000/score \
    --request POST \
    --header "Content-Type: application/json" \
    --data '{"X": [1, 2]}
```

**Expected Response**

```bash
{"score":[1,2]}
```

## Cleanup

With a GKE cluster running, you can create and delete resources with the `kubectl`
command-line client.

To remove your cluster, select the [checkbox][spotlight-instance-checkbox] next
to the cluster name and click the [**Delete**][spotlight-delete-button] button.

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-instance-checkbox]: walkthrough://spotlight-pointer?cssSelector=.p6n-checkbox-form-label
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
