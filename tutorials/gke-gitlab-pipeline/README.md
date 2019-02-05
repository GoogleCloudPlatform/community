# CI/CD to GKE using Gitlab

In this article we’ll build a **continuous integration and deployment pipeline** into a managed  **Google Kubernetes Engine**.  This tutorial will show use of  (1) gitlab.com for the pipeline, (2) Google Cloud for the Kubernetes, and (3) Java Spring Boot for the microservices application.  This article assumes that you have some familiarity with Google Cloud Platform, Kubernetes, Linux and Spring. 

## Core setup

1. Download the code from github at [this](https://github.com/nlonginow/demo-kubernetes-pipeline) link.
2. Create a new project on gitlab.com and connect your local code to it.

```bash
cd folder_containing_downloaded_code
git init
git remote add origin https://gitlab.com/<me>/<repo>.git
git add .
git commit -m "Initial commit"
git push -u origin master
```
where "me" and "repo" are replaced with the correct tags for your repository.

3. Turn on **Auto-Devops**. This will cause Gitlab to run our pipeline on each checkin to the repository.  In your Gitlab project, go to Settings  > CI/CD and expand out the Auto DevOps section.  Check the box as shown.
4. Setup **Gitlab CI/CD environment variables**. We’ll need 3 variables, (1) GOOGLE_KEY, which will be used to enable the pipeline in Gitlab to execute commands against our Kubernetes cluster on our behalf, (2) REGISTRY_PASSWD, which is your password to the Gitlab repository where we store the containers built by our pipeline, and (3) TEST_ONE_KEYWORD, which is simply an output-matching text phrase for use in the smoke test portion of our pipeline. Use "alive" for the third variable.  We'll get the value for the GOOGLE_KEY from a series of actions in Google Cloud Platform.   
5. The **GOOGLE_KEY** value.  This is the key representing a service account in Google Cloud Platform which is authorized to do specific actions relative to the Kubernetes cluster.  It represents a  **_Service Account_** in GCP.  For this step, you’ll need a Google Cloud Platform account and project (if you don’t already have one, follow  [these](https://developers.google.com/maps/premium/devconsole-access#creating_a_google_account) steps to get that in place). If you have your account and project ready, go to your cloud console for the project you want to use, and select IAM & Admin  -- Service Account.  Click ***Create Service Account***.  Give this account some permissions.  We will give it *Compute Engine admin*, so it can update our cluster as part of the pipeline. Click Continue and then click Create Key.  Select *JSON* in the next screen, and save the file locally.   Finally, go back to your Gitlab project, select Settings  -- CICD  -- Environment Variables and set the value for the variable *GOOGLE_KEY* by pasting in the entire contents of the JSON file into the box next to it.  ***Click Save.***
6.  
## The Gitlab Pipeline

We now have credentials in place for operating a pipeline of code delivery into Google Cloud Kubernetes Engine. Let’s build the actual pipeline now. A Gitlab pipeline is specified by a  *.gitlab-ci.yml* file which  **must** be located in the **root** of the repository.  If Gitlab finds that file, it will kick off the pipeline on each commit to the repository.


> Notice that Gitlab pipelines use Docker containers to run each stage, so we need "Docker in Docker" as our primary service.
> 
Here is the front of that file.  
```python
image: docker:latest
services:
  - docker:dind

variables:
  DOCKER_DRIVER: overlay
  SPRING_PROFILES_ACTIVE: gitlab-ci

stages:
  - build
  - package
  - warmup
  - deploy
  - test
  - teardown
```

The pipeline has 6 stages, all executed in sequence if the preceding stage was successful.  Each one runs in a docker container, using an image we specify for the type of work in that stage.

The first 2 stages build, package (containerize) and then store the application on Gitlab’s repository.

```python
maven-build:
  image: maven:3-jdk-8
  stage: build
  script: "mvn package -B -DskipTests spring-boot:repackage"
  artifacts:
    paths:
      - target/*.jar

docker-build:
  stage: package
  script:
  - docker build -t registry.gitlab.com/nlonginow/demo-k8s-frontend .
  - docker login -u gitlab-ci-token -p $CI_BUILD_TOKEN registry.gitlab.com
  - docker push registry.gitlab.com/nlonginow/demo-k8s-frontend
```
Once our code is built and successfully packaged as a Docker container and stored in our repository, we are ready to prepare our test environment.  Notice that our pipeline exists entirely to test a code checkin against an integration environment, not just a simple set of jUnit tests. 

To do this, we spin up a cluster and deploy/test our new code there. This is the purpose of the *warmup* stage.  Here, we are scaling up our deployment and testing cluster.  Our cluster is always alive, but is kept at 0 nodes when not in use, to save resource cost. In GCP Kubernetes Engine the nodes are actually VMs, and while they are running we incur cost.  So, when we are not testing new code, we reduce the nodes to 0, so no VMs are running.  The cluster is still alive, it just have far fewer resources allocated.

> This stage will use a Google Cloud console docker image, since we will be executing Google Cloud commands.

```python
warmup:
  image: google/cloud-sdk
  stage: warmup 
  script:
  - echo "$GOOGLE_KEY" > key.json
  - gcloud auth activate-service-account --key-file key.json
  - gcloud config set compute/zone us-central1-a
  - gcloud config set project YOUR_PROJECT
  - gcloud config set container/use_client_certificate True
  - gcloud config unset container/use_client_certificate  # test line
  - gcloud container clusters get-credentials mycluster
  - gcloud container clusters resize mycluster --size 3 --quiet --zone us-central1-a 

```

This step may take a few minutes while the nodes spin up.

> Note how we are making use of the environment variable GOOGLE_KEY in order to authorize the pipeline actions.

Now we have a running cluster with 3 nodes. The next step deploys our microservice Java Spring application container to the cluster.

```python
k8s-deploy:
  image: google/cloud-sdk
  stage: deploy
  script:
  - echo "$GOOGLE_KEY" > key.json
  - gcloud auth activate-service-account --key-file key.json
  - gcloud config set compute/zone us-central1-a
  - gcloud config set project YOUR_PROJECT 
  - gcloud config set container/use_client_certificate True
  - gcloud config unset container/use_client_certificate  
  - gcloud container clusters get-credentials mycluster 
  - if kubectl get secrets | grep registry.gitlab.com; then kubectl delete secret registry.gitlab.com; fi 
  - kubectl create secret docker-registry registry.gitlab.com --docker-server=https://registry.gitlab.com --docker-username=YOUR_GITLAB_USERNAME --docker-password=$REGISTRY_PASSWD --docker-email=YOUR_EMAIL
  - kubectl apply -f frontend-deployment.yaml
  - kubectl delete pods -l app=demo-k8s-frontend
```

Once this succeeds, we have our microservice container deployed to the pod(s) in our cluster.  The definition of those pods is based on deployment files, which we look at in detail below.

**Now we are ready to test** the running application.  A couple things of note in this step are that we need an IP and port for running a REST test against the application. Instead of hard coding those values into the script (and Java code) we are using a concept of Kubernetes called a *Deployment* and  [ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) to store them. 

We use standard Google Cloud console linux commands to describe those objects, and then some standard linux tools to parse out the needed information. The entire point of the test script is to gather the IP and Port details by inspecting Kubernetes, and then using those values as parameters to a simple smoke test command file. The smoke test executes a curl command against our web application, and looks for a specific string in the output.

Here is the smokeTest file.
```bash
#!/bin/sh
webserv=$1
keyword=$2
echo "curl " http://$webserv " | grep '" $keyword "'"
if curl http://"$webserv"/health | grep "$keyword" > /dev/null
then
    # if the keyword is in the content
    echo "success" 
    exit 0
else
    echo "error"
    exit 1 
fi

```

Finally, now that our pipeline has built, containerized, deployed and tested (live) our microservice application, we want to reduce our cluster size to 0 so as to avoid incurring additional costs.
```puthon
teardown:
  image: google/cloud-sdk
  stage: teardown 
  script:
  - echo "$GOOGLE_KEY" > key.json
  - gcloud auth activate-service-account --key-file key.json
  - gcloud config set compute/zone us-central1-a
  - gcloud config set project YOUR_PROJECT
  - gcloud config set container/use_client_certificate True
  - gcloud config unset container/use_client_certificate  # test line
  - gcloud container clusters get-credentials mycluster
  - gcloud container clusters resize mycluster --size 0 --quiet --zone us-central1-a
```

> Note that this is only the pipeline for deploying a single service.  The code in this example includes a pair of services (and containers) that get built and deployed in their own respective repositories.  i.e., we only build the code for a microservice when that particular microservice has changed.

## The Kubernetes Components

Now, let’s take a look at the Kubernetes objects.  There are 3 components to our Kubernetes application, (1) a  _ConfigMap_ for storing basic variables, (2) a  _Service_, for enabling ingress to our application from the outside world, and (3) a  *deployment* specifying the number of replicas (pods) that we want to deploy for our microservice.  Here are the files.

```python
kind: ConfigMap
apiVersion: v1
metadata:
 name: kubedns-config
 namespace: default
data:
 staff.dns: demo-k8s-staff 
 staff.port: "8080"
 frontend.port: "8081"
```
> Note that we used some of this information previously in our pipeline.  We will also use in our Java Spring application, so that it is not hard-coded anywhere.

Next, the Service.  We are deploying a  LoadBalancertype service on port 8081, which will provide us with an externally accessible IP.  This is not the least expensive way to access a pod, but for purposes of this demonstration it is the simplest.  Look into an  [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) service for a less expensive approach.

```python
kind: Service
apiVersion: v1
metadata:
  name: demo-k8s-frontend
spec:
  selector:
    app: demo-k8s-frontend
  ports:
  - protocol: TCP
    port: 8081
    name: theport
  type: LoadBalancer 
```
And, the deployment of the pods themselves.  Note that the pod specification includes a reference to the ConfigMap elements defined earlier, which makes that information globally available to the code running in the pod (container).  Again, note that the registry details for gitlab are for my own project; your project will have your own details.

```python
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-k8s-frontend
spec:
  selector:
      matchLabels:
        app: demo-k8s-frontend
  replicas: 1 
  template:
    metadata:
      labels:
        app: demo-k8s-frontend
    spec:
      containers:
        - name: demo-k8s-frontend
          image: registry.gitlab.com/nlonginow/demo-k8s-frontend
          ports:
            - containerPort: 8081
          env:
          - name: STAFF_DNS 
            valueFrom:
              configMapKeyRef:
                name: kubedns-config
                key: staff.dns
          - name: STAFF_PORT
            valueFrom:
              configMapKeyRef:
                name: kubedns-config
                key: staff.port
```

## The microservices (Java Spring Boot)

All of our work up till now has assumed we have an application to containerize and deploy to Kubernetes.  Now, let’s look at the application itself.  It’s a standard Spring Boot web application which represents a front-end to a 2-tier application (ie., having a backend container to operate against).

We’ll just look at the Controller class.  The rest of it is quite standard.

```java
@RestController
class OutingController {

	private final OutingRepository repository;
	Logger log = LoggerFactory.getLogger(OutingController.class);
	@Value("${STAFF_DNS:empty}")
	private String configMapStaffDns;
	@Value("${STAFF_PORT:empty}")
	private String configMapStaffPort;


	OutingController(OutingRepository repository) {
		this.repository = repository;
	}
	
	@GetMapping("/ping")
	String ping() {
		return "frontend";
	}

	@GetMapping("/health")
	String getHealth() {
                // Get some info into StackDriver logs...		
		log.info("ConfigMap Dns: " + this.configMapStaffDns);
		log.info("ConfigMap Port: " + this.configMapStaffPort);
		String resourceUrl = "http://" + configMapStaffDns + ":" + configMapStaffPort + "/health";

		log.info("Calling health url: " + resourceUrl);
		log.error("Testing Error log");
		log.warn("Testing Warn level");
		
		RestTemplate restTemplate = new RestTemplate();
		ResponseEntity<String> response = restTemplate.getForEntity(resourceUrl, String.class);
		return response.getBody();
	}

```

Our application is a simple set of 2 microservices which communicate with each other, the first being one accessed by the outside world (via the LoadBalancer IP), and the second being that which is called into from the first one.  

> We use Kube DNS to discover the second container.

What we want to especially observe here is that we retrieved our value for the URL related to our backend service via the ConfigMap, and also the port for that service.  Thus, no hardcoding in the java files, or copying values in multiple places.  The ConfigMap in our deployment file provided these values as global environment variables to any container running in that pod’s deployment.
All your files are listed in the file explorer. You can switch from one to another by clicking a file in the list.

> You can see the logs in GCP Stackdriver Logging by setting the filter to "GKE Container, mycluster, default", and the applying a text filter of "text:"ConfigMap""
## Conclusion
In this article we saw how to build a Gitlab.com pipeline for continuous delivery of a Java Spring microservices application into a Google Cloud Kubernetes engine.




