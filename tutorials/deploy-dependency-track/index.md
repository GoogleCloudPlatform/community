---
title: Deploy OWASP Dependency-Track to Google Cloud
description: Learn how to deploy the OWASP Dependency-Track system to Google Kubernetes Engine.
author: dedickinson
tags: owasp, dependency track, kubernetes, cloud build, cloud sql, supply chain
date_published: 2021-06-11
---

Duncan Dickinson | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you deploy [Dependency-Track](https://dependencytrack.org/) to Google Cloud
and use it to alert you to vulnerabilities in a small Python demonstration system.

The [OWASP Dependency-Track project](https://owasp.org/www-project-dependency-track/)
is a component analysis platform for tracking dependencies, their licenses, and associated vulnerabilities.
Dependency-Track is a useful tool as you build out your software supply chain.

Dependency-Track accepts software bills of materials (SBOMs) in [CycloneDX](https://cyclonedx.org/)
format, which you can provide either on an ad-hoc basis or as part of your deployment system.
The approach is useful in a number of scenarios:

- Software vendors can provide you SBOMs when they deliver a software project.
- Teams building and deploying software can submit SBOMs when new versions are deployed.
- You can manually list dependencies for legacy systems.

Using Dependency-Track helps you to monitor and respond to vulnerabilites in components in your systems.
[Using components with known vulnerabilities](https://owasp.org/www-project-top-ten/2017/A9_2017-Using_Components_with_Known_Vulnerabilities)
is one of the [top 10 web application security risks](https://owasp.org/www-project-top-ten/) identified by the Open Web Application Security Project (OWASP). 
If you have an inventory of components in use across your environment, then you can use resources such as the
[National Vulnerability Database](https://docs.dependencytrack.org/datasources/nvd/)
to determine whether you have vulnerable components, and respond according to your organization's processes.

You run the commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell). This tutorial assumes that you are comfortable running commands in a 
Linux command shell.

This tutorial takes approximately 2-4 hours to complete.

## Architecture overview

The following diagram illustrates the architecture of the solution described in this tutorial:

![Architecture overview.](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/deploy_gke.png)

- The Dependency-Track Frontend and API Service components are hosted as GKE pods.
- Cloud Load Balancing manages traffic to the GKE pods.
- Artifact Registry hosts the container images.
- The GKE instance operates as a private cluster, so Cloud NAT handles outbound requests (primarily Dependency-Track downloading its 
  various data sources).
- A PostgreSQL Cloud SQL database holds Dependency-Track data.
- Secret Manager securely stores database passwords.

## Objectives

1. Generate a bill of materials (BOM) for a basic project.
1. Set up Artifact Registry and prepare the Dependency-Track images.
1. Deploy Dependency-Track to Google Kubernetes Engine. 
1. Upload a BOM and integrate Cloud Build.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Artifact Registry](https://cloud.google.com/artifact-registry)
*   [Container Analysis](https://cloud.google.com/container-analysis/docs/container-analysis)
*   [External IP addresses](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address)
*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Cloud SQL](https://cloud.google.com/sql/)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

You need access to a domain for which you can create two subdomains, one for the frontend and one for the API server. If you do not have a domain,
you can register one with [Google Domains](https://domains.google.com).

### Set up your Google Cloud project

To complete this tutorial, you need a
[Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project).
We recommend that you create a new project specifically for this tutorial.

You must have the [project owner](https://cloud.google.com/iam/docs/understanding-roles#basic-definitions) role for the project.

1.  In [Cloud Shell](https://cloud.google.com/shell), set a project ID environment variable, replacing `[YOUR_PROJECT_ID]` with your
    [Google Cloud project ID](https://cloud.google.com/resource-manager/docs/creating-managing-projects#before_you_begin):

        export GCP_PROJECT_ID=[YOUR_PROJECT_ID]

1.  Set the working project for the `gcloud` environment:

        gcloud config set project $GCP_PROJECT_ID

1.  Set an environment variable for your Google Cloud region:

        export GCP_REGION=us-central1

### Get the tutorial files

1.  Clone the tutorial repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/deploy-dependency-track
        
### Install `pip` and `poetry` packages

1.  Upgrade `pip`:

        pip3 install --upgrade pip

1.  Install `poetry`, a package for dependency management:

        python3 -m pip install poetry --user
        
1.  Add the installation directories to your `PATH` variable so that you can run the installed software:

        export PATH=$PATH:$HOME/.local/bin

## Generate a software bill of materials

The demonstration project has no functional code; its purpose is to include the `flask` library and a very old version of the `django` library, to
demonstrate the presence of a vulnerability.

__WARNING__: The demonstration project includes a very old version of Django with known vulnerabilities. Do not try to run the project. It is only set up to
demonstrate Dependency-Track's ability to report on vulnerabilities.

The [CycloneDX](https://cyclonedx.org/) project defines a schema for software bills of materials (SBOMs), as well as providing 
[tools](https://cyclonedx.org/tool-center/) that you can use with various programming languages and CI/CD tools.

The Python version ([`cyclonedx-bom`](https://pypi.org/project/cyclonedx-bom/)) is included as a development dependency of the demonstration project. 

1.  Go to the demonstration project directory:

        cd demo-project

1.  Install the demonstration project with `poetry`:

        poetry install

1.  Show the project's dependencies:

        poetry show --tree

    The following is an excerpt of the dependency graph output:
    
        django 1.2 A high-level Python Web framework that encourages rapid development and clean, pragmatic design.
        flask 1.1.2 A simple framework for building complex web applications.
        ├── click >=5.1
        ├── itsdangerous >=0.24
        ├── jinja2 >=2.10.1
        │   └── markupsafe >=0.23 
        └── werkzeug >=0.15

1.  Use `poetry` to generate a `requirements.txt` file:

        poetry export --without-hashes>requirements.txt

1.  Generate a CycloneDX BOM in JSON format:

        poetry run cyclonedx-py -j

    `cyclonedx-py` processes the `requirements.txt` file to produce the `bom.json` file.

1.  View the `bom.json` file in a text editor.

    The following is an excerpt that shows the details for the `flask` component, including its name, publisher, version, licenses,
    and [package URL (purl)](https://github.com/package-url/purl-spec): 

        {
            "description": "A simple framework for building complex web applications.",
            "hashes": [
                {
                    "alg": "MD5",
                    "content": "1811ab52f277d5eccfa3d7127afd7f92"
                },
                {
                    "alg": "SHA-256",
                    "content": "8a4fdd8936eba2512e9c85df320a37e694c93945b33ef33c89946a340a238557"
                }
            ],
            "licenses": [
                {
                    "license": {
                        "name": "BSD-3-Clause"
                    }
                }
            ],
            "modified": false,
            "name": "flask",
            "publisher": "Armin Ronacher",
            "purl": "pkg:pypi/flask@1.1.2",
            "type": "library",
            "version": "1.1.2"
        }

## Prepare the Dependency-Track images

In this section, you work with two images:

- The `frontend` image provides the web-based user interface.
- The `apiserver` image provides an Open API-based interface that is used by the frontend and when 
  interacting with Dependency-Track from other systems (such as submitting a BOM).

In this tutorial, you use the [Artifact Registry](https://cloud.google.com/artifact-registry) service to store container images,
and you use the [Container Analysis](https://cloud.google.com/container-analysis/docs/container-analysis) service to scan the images for vulnerabilities.

Because Artifact Registry and Container Analysis have associated costs, you could choose to use the images directly from Docker Hub instead of using these 
services. However, there are advantages to using these services in a production system:

* You have a copy of the images local to your project. This protects your environment
  from changes to the images, and the images remain available if Docker Hub becomes unavailable.
* Container Analysis provides [automatic vulnerability scanning](https://cloud.google.com/container-analysis/docs/vulnerability-scanning) 
  on images, which you can use as part of a broader approach to monitoring for vulnerabilities.

You pull the required images from Docker Hub and push them to your repository, using a specific version number for each image instead of using `latest`.
The image indicated by `latest` changes, which can cause issues such as broken integrations. Though the instructions in this section indicate a version that's
current at the time of the writing of this tutorial, you should check to determine whether a newer version is available.

1.  Enable the APIs:

        gcloud services enable artifactregistry.googleapis.com \
                               containerscanning.googleapis.com

1.  Set the default location for image storage:

        gcloud config set artifacts/location $GCP_REGION

1.  Configure the `dependency-track` image repository:

        gcloud artifacts repositories create dependency-track \
          --repository-format=docker \
          --location=$GCP_REGION

        export GCP_REGISTRY=$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/dependency-track

1.  Configure Docker with the required authentication, so that you can push images to the repository:

        gcloud auth configure-docker $GCP_REGION-docker.pkg.dev

1.  Pull the [Dependency-Track API server](https://hub.docker.com/r/dependencytrack/apiserver) image from Docker Hub, and push the image to your
    repository:

        docker pull docker.io/dependencytrack/apiserver:4.2.1
        docker tag docker.io/dependencytrack/apiserver:4.2.1 $GCP_REGISTRY/apiserver:4.2.1
        docker push $GCP_REGISTRY/apiserver:4.2.1

1.  Pull the [Dependency-Track Front End (UI)](https://hub.docker.com/r/dependencytrack/frontend) image from Docker Hub, and push the image to your
    repository:

        docker pull docker.io/dependencytrack/frontend:1.2.0
        docker tag docker.io/dependencytrack/frontend:1.2.0 $GCP_REGISTRY/frontend:1.2.0
        docker push $GCP_REGISTRY/frontend:1.2.0  

1.  Check your image collection:

        gcloud artifacts docker images list $GCP_REGISTRY
        
    You can use this command at any time to see what images you have stored with Artifact Registry.

## Deploy to Google Kubernetes Engine and Cloud SQL

In this section, you configure the system to run on Google Kubernetes Engine (GKE) and use a Cloud SQL PostgreSQL database. 

### Enable services and set up the environment

1.  Enable the Compute Engine, GKE, Cloud SQL, Cloud SQL Admin, Secret Manager, and Service Networking services:

        gcloud services enable compute.googleapis.com \
                               container.googleapis.com \
                               sql-component.googleapis.com \
                               sqladmin.googleapis.com \
                               secretmanager.googleapis.com \
                               servicenetworking.googleapis.com

1.  Designate a default region for Compute Engine, which runs the GKE worker nodes:

        gcloud config set compute/region $GCP_REGION

1.  Add your domains to the commands below: 

        export DT_DOMAIN_API=[YOUR_DOMAIN_NAME_FOR_THE_API_SERVER]
        export DT_APISERVER=https://$DT_DOMAIN_API
        export DT_DOMAIN_UI=[YOUR_DOMAIN_NAME_FOR_THE_FRONTEND]

    * `DT_DOMAIN_API` provides the API Server (e.g., `api.example.com`).
    * `DT_APISERVER` is its URL (e.g., `https://api.example.com`).
    * `DT_DOMAIN_UI` provides the frontend (e.g., `ui.example.com`).

### Create TLS certificates

In this section, you create TLS certificates for the API and user interface endpoints. You could do this using a
[GKE `ManagedCertificate` resource](https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs#setting_up_the_managed_certificate),
but defining the TLS certificates outside of Kubernetes allows you to transfer them as needed. This isn't an important requirement for a tutorial environment,
but you should consider this advantage for your production environment.

The provisioning of the certificates can take a long time, so it's best to get these started early.

1.  Create the TLS certificate for the API server:

        gcloud compute ssl-certificates create dependency-track-cert-api \
          --description="Certificate for the Dependency-Track API" \
          --domains=$DT_DOMAIN_API \
          --global

1.  Create the TLS certificate for the frontend:

        gcloud compute ssl-certificates create dependency-track-cert-ui \
          --description="Certificate for the Dependency-Track UI" \
          --domains=$DT_DOMAIN_UI \
          --global

1.  Check the progress:

        gcloud compute ssl-certificates list
        
    You can check the progress at any time with this command.

While waiting for the certificates to be provisioned, you can continue with the next sections of the tutorial. The setup of the certificates only completes when
they're aligned to a load balancer.

### Create external IP addresses

1.  Create two external IP addresses:

        gcloud compute addresses create dependency-track-ip-api --global
        gcloud compute addresses create dependency-track-ip-ui --global

1.  Set two environment variables, one for each of the external IP addresses:

        export DT_IP_API=$(gcloud compute addresses describe dependency-track-ip-api \
          --global --format="value(address)")
      
        export DT_IP_UI=$(gcloud compute addresses describe dependency-track-ip-ui \
          --global --format="value(address)")

1.  Check the addresses:

        echo "IP address for $DT_DOMAIN_API: $DT_IP_API"
        echo "IP address for $DT_DOMAIN_UI: $DT_IP_UI"

### Configure your domains

Add your domain names and the IP addresses to your DNS system. DNS entries can take up to 48 hours to propagate. 

For this tutorial, you need to create two subdomains, one for the frontend and one for the API server.

To configure your domains, create an `A` record with a `TTL` (time to live) of 1 hour
using the subdomain in the record's `Name` field and the IP address in the record's
`Data` Field. The Google Domains site provides a guide to
[resource records](https://support.google.com/domains/answer/3251147), and your hosting service should 
offer similar guidance.

For example, if you use the `api` subdomain for the Dependency-Track API Server and `dt` subdomain for the Dependency-Track user interface, the two resource
records should be configured as follows for your domain:

| Name | Type | TTL | Data |
| ---- | ---- | --- | ---- |
| api  |  A   | 1hr | 1.2.3.4 |
| dt   |  A   | 1hr | 1.2.3.5 |

Be sure to use the actual IP addresses that you created, not the `1.2.3.4` and `1.2.3.5` examples.

With the settings above for the example domain `example.com`, the following domain names would be available:

* `api.example.com` will resolve to `1.2.3.4`.
* `dt.example.com` will resolve to `1.2.3.5`.

### Set up a VPC network for the GKE cluster

In this section, you create a VPC network for the private GKE cluster and to enable
[private service access](https://cloud.google.com/sql/docs/postgres/configure-private-services-access#configure-access), which allows you to create a Cloud SQL
instance without a public IP address.

1.  Create the VPC network:

        gcloud compute networks create dependency-track \
          --description="A demo VPC network for hosting Dependency-Track" \
          --subnet-mode=custom

1.  Reserve an IP address:

        gcloud compute addresses create google-managed-services-dependency-track \
          --global \
          --purpose=VPC_PEERING \
          --prefix-length=20 \
          --network=dependency-track

1.  Connect to the service with VPC peering:

        gcloud services vpc-peerings connect \
          --service=servicenetworking.googleapis.com \
          --ranges=google-managed-services-dependency-track \
          --network=dependency-track \
          --project=$GCP_PROJECT_ID

### Create the GKE cluster

In this section, you create a private GKE cluster, but the Kubernetes control plane is available on a public endpoint. For this tutorial, this allows you
to access the cluster with `kubectl` from Cloud Shell. In a production environment, you should typically limit access to the control plane. For details, 
see [Access to cluster endpoints](https://cloud.google.com/kubernetes-engine/docs/concepts/private-cluster-concept#overview).

1.  Create the GKE cluster:

        gcloud container clusters create-auto dependency-track \
          --region=$GCP_REGION \
          --create-subnetwork="name=dependency-track-subnet" \
          --network=dependency-track \
          --no-enable-master-authorized-networks \
          --enable-private-nodes

1.  Set up `kubectl` with the correct credentials:

        gcloud container clusters get-credentials dependency-track --region $GCP_REGION

1.  Check the client and server versions:

        kubectl version

    If this command returns details for the client and server, `kubectl` was able to connect to the GKE cluster. If the command
    returns `Unable to connect to the server`, then see 
    [Configuring cluster access for kubectl](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl)
    for help.

### Set up Cloud NAT

The GKE nodes need outbound internet access so that the Dependency-Track system can download its required databases. This requires Cloud NAT for network address
translation.

1.  Create a router:

        gcloud compute routers create dependency-track-nat-router \
          --network dependency-track \
          --region $GCP_REGION

1.  Add a Cloud NAT gateway:

        gcloud compute routers nats create dependency-track-nat \
          --router=dependency-track-nat-router \
          --auto-allocate-nat-external-ips \
          --nat-all-subnet-ip-ranges \
          --region $GCP_REGION \
          --enable-logging

### Create a Kubernetes namespace

1.  Create a `dependency-track` Kubernetes namespace:

        kubectl create namespace dependency-track
        
1.  Switch the context to the new namespace:

        kubectl config set-context --current --namespace=dependency-track

### Deploy the Dependency-Track frontend

The deployment process uses the [`kustomize`](https://kubectl.docs.kubernetes.io/guides/introduction/)
functionality built into the `kubectl` package. 

The various deployment files are in the `deploy` directory.

The `envsubst` command is used to process environment variables in the deployment files. The required package (`gettext-base`) is already installed
in Cloud Shell.

To deploy the frontend workload to the GKE cluster, run the following commands
from the base directory of the tutorial:

    cd deploy/frontend
    cat kustomization.base.yaml | envsubst >kustomization.yaml
    kubectl apply -k .

### Set up a service account for database access

The API Server needs to access a database. In this section, you create a service account for database access with GKE
[workload identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity), which is used by a PostgreSQL database that you
create in the next section. This allows the [SQL Auth Proxy pod](https://cloud.google.com/sql/docs/postgres/connect-kubernetes-engine) to
connect to Cloud SQL through the service account.

1.  Create a Kubernetes service account:

        kubectl create serviceaccount dependency-track

1.  Create a Google Cloud IAM service account:

        gcloud iam service-accounts create dependency-track

1.  Align the Kubernetes service account to the IAM service account:

        gcloud iam service-accounts add-iam-policy-binding \
          --role roles/iam.workloadIdentityUser \
          --member "serviceAccount:$GCP_PROJECT_ID.svc.id.goog[dependency-track/dependency-track]" \
          dependency-track@$GCP_PROJECT_ID.iam.gserviceaccount.com

1.  Align the IAM service account to the Kubernetes service account:

        kubectl annotate serviceaccount \
          --namespace dependency-track \
          dependency-track \
          iam.gke.io/gcp-service-account=dependency-track@$GCP_PROJECT_ID.iam.gserviceaccount.com
  
1.  Grant the `cloudsql.client` role to the IAM service account so that SQL Auth Proxy can connect to the database:

        gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
          --role roles/cloudsql.client  \
          --member "serviceAccount:dependency-track@$GCP_PROJECT_ID.iam.gserviceaccount.com"

### Set up a Cloud SQL instance using PostgreSQL

1.  Generate a random password for each database account and store it in [Secret Manager](https://cloud.google.com/secret-manager):

        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 30 | head -n 1 | \
          gcloud secrets create dependency-track-postgres-admin \
          --data-file=-

        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 30 | head -n 1 | \
          gcloud secrets create dependency-track-postgres-user \
          --data-file=-

1.  Set a variable for the database instance name:

        export DT_DB_INSTANCE=dependency-track

1.  Create the Cloud SQL instance:

        gcloud beta sql instances create $DT_DB_INSTANCE \
          --region=$GCP_REGION \
          --no-assign-ip \
          --network=projects/$GCP_PROJECT_ID/global/networks/dependency-track \
          --database-version=POSTGRES_13 \
          --tier=db-g1-small \
          --storage-auto-increase \
          --root-password=$(gcloud secrets versions access 1 --secret=dependency-track-postgres-admin)          

    Creating a new Cloud SQL instance can take several minutes.
    
    At time of writing, the private IP addresses for Cloud SQL feature is in preview, so it requires the `gcloud beta sql instances create` command.

1.  Set up a database user:

        gcloud sql users create dependency-track-user \
          --instance=$DT_DB_INSTANCE \
          --password=$(gcloud secrets versions access 1 --secret=dependency-track-postgres-user)

1.  Create the database:

        gcloud sql databases create dependency-track \
          --instance=$DT_DB_INSTANCE

1.  Set a variable for the connection details:

        export DT_DB_CONNECTION=$(gcloud sql instances describe $DT_DB_INSTANCE --format="value(connectionName)")

1.  Set the databse password as a Kubernetes secret for the API server:

        kubectl create secret generic dependency-track-postgres-user-password \
          --from-literal ALPINE_DATABASE_PASSWORD=$(gcloud secrets versions access 1 --secret=dependency-track-postgres-user) 

### Deploy and start the API server

To deploy the API server workload to the GKE cluster, run the following commands:

    cd ../api
    cat kustomization.base.yaml | envsubst >kustomization.yaml
    kubectl apply -k .

Though the `kubectl apply` command returns very quickly, the GKE cluster needs to resize for the new workload, which can take a few minutes.
Also, the API Server loads a lot of data and can take several minutes to be ready. 

To check that the required pods have been deployed, run the following command:

    kubectl get pods -w -l app=dependency-track-apiserver

When the pod's status is listed as `RUNNING` with `2/2` containers ready, exit by pressing `Ctrl+C`.

To track the progress of the API server's data load, open a separate Cloud Shell terminal and check the logs with this command:

    kubectl logs -f dependency-track-apiserver-0 dependency-track-apiserver

### Troubleshooting

#### TLS error

If you visit the frontend or API Server you might get a TLS error such as `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`.
Check the TLS certificate status with `gcloud compute ssl-certificates list` - you need both of the
certificates to be listed as "ACTIVE". If you see "FAILED_NOT_VISIBLE" just wait a while for the certificate to
be provisioned to the load balancer. This can take some time (up to 60-minutes).

It can be useful to open a new terminal and set a watch on the certificate listing:

```bash
watch -n 30 gcloud compute ssl-certificates list
```

Check out 
[Troubleshooting SSL certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates/troubleshooting)
for more info.

#### GKE Connectivity

If needed, you can check out the cluster by firing up a `busybox` instance: 

```bash
kubectl run --rm -it --image=busybox -- sh
```

Then run something like: `wget -O - http://www.example.com`

#### Checking the database

If you need to check the database using the `psql` tool, start by reviewing
[Connecting using the Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-admin-proxy)

You can install `psql` in Cloud Shell (if it's not already there) with:

```bash
sudo apt install postgresql-client
```

Next, start up a Cloud SQL Auth Proxy in your GKE cluster with the following command:

```bash
kubectl run proxy --port 5432 --serviceaccount=dependency-track \
  --image=gcr.io/cloudsql-docker/gce-proxy:1.22.0 -- /cloud_sql_proxy \
    -instances=$DT_DB_CONNECTION=tcp:5432 \
    -ip_address_types=PRIVATE
```

Setup a port forwarding on the Postgres port with:

```bash
kubectl port-forward pod/proxy 5432:5432
```

You can now open a new terminal and connect to the Postgres instance with:

```bash
psql "host=127.0.0.1 sslmode=disable dbname=dependency-track user=dependency-track-user"
```

Don't leave the pod hanging around - delete it once you're done:

```bash
kubectl delete pod/proxy
```

## Using Dependency-Track

The API Server loads a range of data and will take up to half an hour to be ready.
You may also need to wait for the TLS certificates to be provisioned.

When the API Server is ready, you can now visit the API Server site.
The following paths may be of interest:

- `/api/version` - the service version
- `/api/swagger.json` - the OpenAPI definition

Once you have the Dependency-Track API and frontend running, you're ready to login to the frontend.

Once you've accessed the frontend, enter `admin`/`admin` for the initial login 
username/password - you'll be prompted to set up a better password. 
Refer to 
[Dependency-Track's Initial Startup document](https://docs.dependencytrack.org/getting-started/initial-startup/)
for more information.

In the frontend user interface, go to the "Projects" screen and click on "+ Create Project".

![New project screen](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/new_project.png)

You don't need to enter many details, just use "demo-project" for the Project Name
and set the Classifier to "Application" then press the "Create" button.

![New project dialog](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/new_project_dialog.png)

You'll see the new project listed - click on it and when in the project screen, 
click on the "Components" tab. 

You will need a local copy of `bom.json` in order to upload it. Use the following
command in the base of the tutorial directory to download a copy to your computer
(_make sure you're in the `demo-project` directory_):

```bash
cloudshell download bom.json
```

You can now click on the "Upload BOM" button and select the `bom.json` file for upload.

![Uploading the BOM](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/upload_bom.png)

When you return to the project screen you should see the components listed. If not,
click on the refresh button to the right of the screen. Take some time to click around
and explore the information. 

![Project screen with components listed](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/component_listing.png)

The `django` component has a high risk score and seems to be the source 
of several issues. If you click on the `django` link, you'll be taken to 
the overview page for the component. Here you'll see that `django` 1.2
has numerous known vulnerabilities: 1 Critical, 3 High, 27 Medium and 1 Low.

![Project screen with components listed](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/component_listing_overview.png)

Clicking on the `Vulnerabilities` tab will then take you to the listing for
all the known component vulnerabilities. You can then click through to each 
vulnerability (such as "CVE-2011-4137") to get further details about the vulnerability.

![Project screen with components listed](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/component_listing_vulns.png)

### Uploading a BOM from the terminal

Uploading a BOM manually is not a long-term solution. Let's take a look at how a BOM
can be directly uploaded to the API. 

In the frontend user interface, go to the "Administration" screen, and select 
"Access Management" (last item), then "Teams".
You'll see a team named "Automation", click on this to view the team's configuration.

![The Teams listing screen](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/teams.png)

Add `PROJECT_CREATION_UPLOAD` permission to the "Automation" team.

![The permissions listing for the team](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/teams_perm.png)

Copy the API Key that is displayed for the "Automation" team 
and set up the API Key as a variable in your terminal:

```bash
export DT_API_KEY=<YOUR API KEY>
```

Once you've set up the "Automation" team's permissions and API key you're ready
to upload a BOM to your Dependency-Track service. 

Generate and upload the XML version of the BOM:

```bash
# 1. Generate the BOM
poetry install
poetry export --without-hashes>requirements.txt
poetry run cyclonedx-py

# 2. Upload the BOM
poetry run ./bom-loader.py --url $DT_APISERVER --api-key=$DT_API_KEY
```

The `bom-loader.py` script performs the following:

1. Reads the project name and version from the `pyproject.toml` file
1. Loads the BOM (`bom.xml`)
1. Packages the information and submits it to the Dependency-Track API server

Now you can go to your Dependency-Track frontend and open the "Projects" tab. You'll
see there's now a `demo-project` with version `0.1.0`:

![Project listing with demo_project version 0.1.0](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/listing_demo_project.png)

As before, you can click on the project and explore the dependencies.

### Using Cloud Build

For the next iteration of submitting a BOM let's look at integrating the approach with
your CI/CD workflow. 

Start by enabling the Cloud Build and Cloud Storage APIs:

```bash
gcloud services enable cloudbuild.googleapis.com \
  storage-component.googleapis.com
```

Next, create a builder image that can be used in Cloud Build. First,
create a new repository called `builders`:

```bash
gcloud artifacts repositories create builders \
              --repository-format=docker \
              --location=$GCP_REGION
```

Next, make sure you're in the `demo-project` directory and submit the 
Poetry image to Cloud Build:

```bash
gcloud builds submit support/poetry-image \
  --tag ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/builders/poetry:1
```

The Cloud Build job will create the image and store it in the `builders` repository.
This image provides Python with the Poetry system ready to go.

If you take a look at the `cloudbuild.yaml` file you'll notice that there's an 
`artifacts` section that will store the generated `bom.xml` in a Cloud Storage 
bucket. This isn't necessary but could be a useful information source.

```yaml
artifacts:
  objects:
    location: gs://${PROJECT_ID}-build/$BUILD_ID
    paths: ["bom.xml"]
```

Create the bucket using the following command:

```bash
gsutil mb gs://${GCP_PROJECT_ID}-build
```

Cloud Build can [use secrets stored in Secret Manager](https://cloud.google.com/build/docs/securing-builds/use-secrets#configuring_builds_to_access_the_secret_from).
This is extremely useful for automating build environments as Secret Manager provides a 
central place for holding sensitive information such as keys and passwords. 
Builds can use this to quickly access required secrets without requiring command line 
parameters. This also make it easier to rotate keys (such as the Dependency-Track API key)
without needing to reconfigure every build.

Start by adding the API Key as a secret:

```bash
printf $DT_API_KEY | gcloud secrets create dependency-track-api-key --data-file -
```

Then grant Cloud Build the ability to read the secret:

```bash
# Get the unique GCP project number
export GCP_PROJECT_NUM=$(gcloud projects describe ${GCP_PROJECT_ID} \
                          --format 'value(projectNumber)')

# Grant the secretAccessor role to the Cloud Build service account
gcloud secrets add-iam-policy-binding dependency-track-api-key  \
    --member serviceAccount:${GCP_PROJECT_NUM}@cloudbuild.gserviceaccount.com \
    --role roles/secretmanager.secretAccessor
```

If you previously uploaded the BOM from the terminal you may want to delete the project/version 
in Dependency-Track before you submit the BOM using Cloud Build. To delete it,
go to the Dependency-Track frontend, select the project from the list and click 
"View Details" in the project screen (below).
The pop-up dialog will have a "Delete" button that deletes the project.

![The View Details link is used to open the display to delete the project](https://storage.googleapis.com/gcp-community/tutorials/deploy-dependency-track/delete_demo_project.png)

With that done you can now submit the build with the following command:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_DT_APISERVER=$DT_APISERVER . 
```

The build will start and push the generated BOM to Dependency-Track.

You can check out the details in the frontend UI or try out the API with `curl`. The following
command will list all projects

```bash
curl --location --request GET \
  "$DT_APISERVER/api/v1/project" \
  --header "x-api-key: $DT_API_KEY" | jq
```

This one provides basic project details:

```bash
curl --location --request GET \
  "$DT_APISERVER/api/v1/project/lookup?name=demo-project&version=0.1.0" \
  --header "x-api-key: $DT_API_KEY" | jq
```

If you visit the API site you'll be able to access the OpenAPI definition for further
API goodness. The address will look something like `https://<DT_DOMAIN_API>/api/swagger.json`.


## Considerations for a production system

Take some time to explore Dependency-Track and consider how and where you might use it. The scenarios provided in this tutorial (manual upload, command-line
upload, and CI/CD integration) are good starting points for including dependency tracking as part of managing your software supply chain.

If Dependency-Track is right for your organization, it's important to consider a production approach to setting up the system.

Though this tutorial demonstrates several aspects of setup and configuration, you need to consider additional aspects for a production implementation,
including the following:

- **Keep your container images up to date**: You got a copy of the Dependency-Track images from Docker Hub and set them up in Artifact Registry with container
  scanning. Make sure to track new releases of Dependency-Track and also consider how to keep your container images updated.
- **Consider your GKE deployment**: This tutorial provides a set of good practices, such as workload identity, Cloud SQL Auth Proxy, and private clusters. 
  For a production instance, you must also plan out aspects such as network setup and how you serve the client and API to your organization. Don't forget to 
  review [access to cluster endpoints](https://cloud.google.com/kubernetes-engine/docs/concepts/private-cluster-concept#overview) to determine whether
  public access to the Kubernetes control plane can be disabled.
- **Review all permissions**: Some of the tutorial configuration needs tightening up for a long-term production service. For example, review the Cloud SQL user,
  because it has very broad access that you can reduce. 
- **Review the Cloud SQL configuration**: Consider aspects such as [automated backups](https://cloud.google.com/sql/docs/postgres/backup-recovery/backing-up) and
  the resources (memory and vCPU) of the underlying virtual machine.
- **Set up access**: Consider how users will access the system. Dependency-Track
  [supports OIDC](https://docs.dependencytrack.org/getting-started/openidconnect-configuration/), which can save you from managing authentication in the 
  Dependency-Track service. You can also explore [Identity-Aware Proxy](https://cloud.google.com/iap) for remote access to the system.
- **Rotate API keys regularly**: Dependency-Track uses API keys for access to the API Server (such as from Cloud Build). Ensure that these keys are rotated 
  regularly.
- **Use security and operations services**: Consider tools such as [Cloud Armor](https://cloud.google.com/armor) and 
  [Google Cloud's operations suite](https://cloud.google.com/products/operations) for the ongoing security and operation of your system.

Having a model to track dependecies is a great first step. Configuring the system to notify you when a vulnerability pops up is even better. Check out the
[Dependency-Track notifications](https://docs.dependencytrack.org/integrations/notifications/) document for options. The webhooks model is a useful approach to 
automating responses. Also consider your processes and how your organization will respond when a vulnerability is reported.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources 
used in this tutorial, you can delete the project.

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

Remove the two domain names (DNS entries) created in the "Create external IP addresses" section.
