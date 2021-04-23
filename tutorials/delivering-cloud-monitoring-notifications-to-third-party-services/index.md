---
title: Deliver Cloud Monitoring notifications to third-party services
description: Learn how to use Cloud Run and Pub/Sub to forward Cloud Monitoring alerts to third-party applications.
author: aprill1,rubenh00
tags: alerting, Terraform, GitHub
date_published: 2020-08-14
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial is for Google Cloud customers who want to deliver [Cloud Monitoring alerts](https://cloud.google.com/monitoring/alerts) to third-party services
that don’t have [supported notification channels](https://cloud.google.com/monitoring/support/notification-options).

Follow this tutorial to write, deploy, and call a Cloud Run service from [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) to pass monitoring 
notifications to any third-party service. The tutorial provides two working examples of integrations ([Philips Hue smart bulbs](https://developers.meethue.com/)
and [self-hosted Jira](https://www.atlassian.com/software/jira/core)) and explains how these examples can be deployed to Google Cloud. Additionally, it explains
steps for continuous integration using [Cloud Build](https://cloud.google.com/cloud-build), [Terraform](https://cloud.google.com/docs/terraform), and GitHub. All 
of the source code for this project can be found in
[this GitHub repository](https://github.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code).

This tutorial assumes that you're familiar with Cloud Monitoring alerting and already have alerting policies in place.

## Objectives

*   Write a service to handle Pub/Sub monitoring notifications and deliver them to a third-party service.
*   Build and deploy the service to Cloud Run using Cloud Build, Terraform, and GitHub.

## Costs

This tutorial uses billable components of Google Cloud:

*   Cloud Build
*   Cloud Storage
*   Cloud Run
*   Pub/Sub
*   Secret Manager

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you've already created:

1.  Select or create a Google Cloud project.

    [Go to the project selector page](https://pantheon.corp.google.com/projectselector2/home/dashboard)

1.  Enable billing for your project.

    [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing)

1.  Enable the Cloud Build, Cloud Run, Resource Manager, Identity and Access Manager (IAM), Container Registry, and Secret Manager API. 

    [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=cloud_build,cloud_run,resource_manager,container_registry,secret_manager)

When you finish this tutorial, you can avoid continued billing by deleting the resources you created. For details, see the "Cleaning up" section at the end of 
this tutorial.

## Looking at the code

The code for this tutorial includes sample integrations for both Philips Hue smart lights and Jira servers. The integration code is located in the
[`philips_hue_integration_example`](https://github.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/tree/dev/philips_hue_integration_example) and
[`jira_integration_example`](https://github.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/tree/dev/jira_integration_example)
directories, respectively.

In both examples, there is a server that handles incoming Pub/Sub messages. The following code in `main.py` sets up a basic Flask HTTP server to handle the 
incoming requests:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/philips_hue_integration_example/main.py /app_config =.*/ /app.config.from_object\(app_config\)/)
```py
app_config = config.load()
logging.basicConfig(level=app_config.LOGGING_LEVEL)

# logger inherits the logging level and handlers of the root logger
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(app_config)
```

Pub/Sub pull subscriptions are also an option, but we chose push for more timely delivery of notifications. More information on pull and push subscriptions can
be found in [Subscriber overview](https://cloud.google.com/pubsub/docs/subscriber#push_pull).

Flask configuration variables are loaded in the `config.py` module. The exact implementation isn’t important, but this is done to centralize configuration
loading and enhance modularity. (The code is available for study in the repository.) It is important to note that configuration variables are either loaded from
environment variables or from Secret Manager. Never check credentials or API keys directly into repository code.

Finally, a Python logger is created and the Flask app is started.

Below is a handler that processes the Pub/Sub message:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/philips_hue_integration_example/main.py /@app.route/ /.*return send_monitoring_notification_to_third_party.*/)
```py
@app.route('/', methods=['POST'])
def handle_pubsub_message():
    pubsub_received_message = request.get_json()

    # parse the Pub/Sub data
    try:
        pubsub_data_string = pubsub.parse_data_from_message(pubsub_received_message)
    except pubsub.DataParseError as e:
        logger.error(e)
        return (str(e), 400)

    # load the notification from the data
    try:
        monitoring_notification_dict = json.loads(pubsub_data_string)
    except json.JSONDecodeError as e:
        logger.error(e)
        return (f'Notification could not be decoded due to the following exception: {e}', 400)

    return send_monitoring_notification_to_third_party(monitoring_notification_dict)
```

The handler calls the `parse_data_from_message()` function in `utilities/pubsub.py` to parse the relevant notification data from the Pub/Sub message, and then 
loads the notification data into a dictionary. This notification dictionary is then passed to `send_monitoring_notification_to_third_party()` which appropriately
notifies the third-party service about the alert with an API client. You can modify this dispatch function to forward alerts to any third-party service; the 
following sections outline two examples to give you an idea how.

Remember to acknowledge the Pub/Sub message on success by returning a success HTTP status code (`200` or `204`). See
[Receiving push messages](https://cloud.google.com/pubsub/docs/push#receiving_push_messages).

Finally, there is a Dockerfile containing instructions to build an image that hosts the Flask server when deployed to Cloud Run:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/philips_hue_integration_example/Dockerfile docker /# \[START/ /# \[END.*/)
```docker
# [START run_pubsub_dockerfile]

# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.8

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy application dependency manifests to the container image.
# Copying this separately prevents re-running pip install on every code change.
COPY requirements.txt ./

# Install production dependencies.
RUN pip install -r requirements.txt

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

ARG PROJECT_ID
ENV PROJECT_ID=$PROJECT_ID

# Run the web service on container startup. 
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

# [END run_pubsub_dockerfile]
```


### Philips Hue

For this Philips Hue integration, when a Cloud Monitoring notification occurs, the Philips Hue light changes to a specific color depending on the policy name
and incident state.

Look at the dispatch function for Philips Hue in `philips_hue_integration_example/main.py`:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/philips_hue_integration_example/main.py /def send_monitoring/ /.*return \(repr\(hue_value\).*/)
```py
def send_monitoring_notification_to_third_party(notification):
    """Send a given monitoring notification to a third party service.

    Args:
        notification: The dictionary containing the notification data.

    Returns:
        A tuple containing an HTTP response message and HTTP status code
        indicating whether or not sending the notification to the third
        party service was successful.
    """

    philips_hue_client = philips_hue.PhilipsHueClient(app.config['BRIDGE_IP_ADDRESS'],
                                                      app.config['USERNAME'])

    try:
        hue_value = philips_hue.get_target_hue_from_monitoring_notification(
            notification, app.config["POLICY_HUE_MAPPING"])
        philips_hue_client.set_color(app.config['LIGHT_ID'], hue_value)
    except philips_hue.Error as e:
        logger.error(e)
        return (str(e), 400)

    return (repr(hue_value), 200)
```

The dispatch function for Philips Hue instantiates a Philips Hue client, sets the color of a Philips Hue light based on the details of the monitoring 
notification, and then returns the appropriate response message and status code.

The Philips Hue client is defined in `philips_hue_integration_example/utilities/philips_hue.py`:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/philips_hue_integration_example/utilities/philips_hue.py /class PhilipsHueClient/ /return response/)
```py
class PhilipsHueClient():
    """Client for interacting with different Philips Hue APIs.

    Provides interface to access Philips Hue lights, groups, schedules, etc.

    Attributes:
        bridge_ip_address: IP address of the Hue bridge system to connect to.
        username: Authorized user string to make API calls.
    """
    def __init__(self, bridge_ip_address, username):
        self._bridge_ip_address = bridge_ip_address
        self._username = username


    @property
    def bridge_ip_address(self):
        return self._bridge_ip_address


    @property
    def username(self):
        return self._username


    def set_color(self, light_id, hue):
        """Sets the color of the light to a specified hue value.

        Args:
            light_id:  The id to pass to the Philips Hue API to
                specify the light to set a color for.
            hue: Hue of the light (corresponding to HSB color system).
                Takes values from 0 to 65535. Programming 0 and 65535
                would mean that the light will resemble the color red,
                25500 for green and 46920 for blue.

        Returns:
            HTTP Response from the Philips Hue API.
        """
        response = requests.put(url=f'http://{self._bridge_ip_address}/api/{self._username}/lights/{light_id}/state',
                                data=json.dumps({"on": True, "hue": hue}))
        if response.status_code != 200:
            raise BadAPIRequestError(response.text)
        return response
```

The Philips Hue client includes necessary properties and functions to interact with the Philips Hue REST API, and also contains the logic for determining the correct hue value to change a light to based on the monitoring notification received in the app request handler. In particular, the mapping between policy names and Philips Hue colors is stored in `philips_hue_integration_example/config.py` and can be changed as desired to modify the behavior of the application. 

### Jira

For this Jira integration, when a Cloud Monitoring notification occurs, a Jira issue is either created or closed. More specifically, if the notification is 
regarding an open incident, a new Jira issue corresponding to the incident is created, and if the notification is about a closed incident, all Jira issues that 
correspond to the incident are closed. To clearly identify which incident a Jira issue corresponds to, each Jira issue created is given a label
`monitoring_incident_id_{ID}`, where `{ID}` is the ID of the incident it is about.

Look at the dispatch function for Jira in `jira_integration_example/main.py`:

[embedmd]:# (https://raw.githubusercontent.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/dev/jira_integration_example/main.py /def send_monitoring_notification/ /return \('', 200\)/)
```py
def send_monitoring_notification_to_third_party(notification):
    """Send a given monitoring notification to a third party service.

    Args:
        notification: The dictionary containing the notification data.

    Returns:
        A tuple containing an HTTP response message and HTTP status code
        indicating whether or not sending the notification to the third
        party service was successful.
    """

    try:
        oauth_dict = {'access_token': app.config['JIRA_ACCESS_TOKEN'],
                      'access_token_secret': app.config['JIRA_ACCESS_TOKEN_SECRET'],
                      'consumer_key': app.config['JIRA_CONSUMER_KEY'],
                      'key_cert': app.config['JIRA_KEY_CERT']}
        jira_client = JIRA(app.config['JIRA_URL'], oauth=oauth_dict)
        jira_integration.update_jira_based_on_monitoring_notification(
            jira_client,
            app.config['JIRA_PROJECT'],
            app.config['CLOSED_JIRA_ISSUE_STATUS'],
            notification)

    except (jira_integration.Error, JIRAError) as e:
        logger.error(e)
        return (str(e), 400)

    return ('', 200)
```

The Jira client comes from the [jira-python API](https://jira.readthedocs.io/en/master/api.html), and it provides functions to interact with a Jira server. In
this example, it is authenticated using OAuth.

The function instantiates a Jira client connected to a Jira server and updates a project on the Jira server via the client based on the monitoring notification.
The `update_jira_based_on_monitoring_notification()` function is responsible for updating a Jira server by either opening or closing issues in a specified 
project based on the status of the incident from the monitoring notification. The Jira status that represents closed issues in the Jira project is loaded from 
the app configurations, since this is not universal for all Jira projects.

## Deploying the app

This section describes how to deploy and set up continuous integration using Cloud Build, Terraform, and GitHub, following the GitOps methodology. The
instructions are based on
[Managing infrastructure as code with Terraform, Cloud Build, and GitOps](https://cloud.google.com/solutions/managing-infrastructure-as-code), which also 
explains the GitOps methodology and architecture. Sections from the guide are also referenced in the steps below. An important difference is that this document
assumes that separate Google Cloud projects are used for the `dev` and `prod` environments, whereas the referenced guide configures the environments as virtual
private clouds (VPCs). As a result, the following deployment steps (with the exception of “Setting up your GitHub repository”) need to be executed for each of
the `dev` and `prod` projects. 

### Set up your GitHub repository

To get all the code and understand the repository structure needed to deploy your app, follow the steps in
[Setting up your GitHub repository](https://cloud.google.com/solutions/managing-infrastructure-as-code#setting_up_your_github_repository). Make sure to replace 
`solutions-terraform-cloudbuild-gitops `with `cloud-monitoring-notification-delivery-integration-sample-code`.

### Provision Google Cloud resources with Terraform

Terraform is a [HashiCorp](https://www.hashicorp.com/) open source tool that enables you to predictably create, change, and improve your cloud infrastructure
using code. In this tutorial, Terraform is used to automatically create and manage necessary resources in Google Cloud.

Terraform creates the following resources in your cloud project:

*   A Cloud Run service called `cloud-run-pubsub-service` to deploy the Flask application
*   A Pub/Sub topic called `tf-topic`
*   A Pub/Sub push subscription called `alert-push-subscription` with a push endpoint to `cloud-run-pubsub-service`
*   A service account with ID `cloud-run-pubsub-invoker` to represent the Pub/Sub subscription identity

In addition, Terraform configures the following authentication policies:

*   Enabling Pub/Sub to create authentication tokens in your Google Cloud project
*   Giving the `cloud-run-pubsub-invoker` service account permission to invoke `cloud-run-pubsub-service`
*   Adding authentication for `alert-push-subscription` using the `cloud-run-pubsub-invoker` service account

These configurations will be applied automatically on source code changes after connecting Cloud Build with GitHub, but can also be run manually on your local 
machine as explained in the `README.md` file of the repository.

#### Configure Terraform to store state in a Cloud Storage bucket

By default, Terraform stores [state](https://www.terraform.io/docs/state/) locally in a file named `terraform.tfstate`. This default configuration can make 
Terraform usage difficult for teams, especially when many users run Terraform at the same time and each machine has its own understanding of the current 
infrastructure.

To help you avoid such issues, this section configures a [remote state](https://www.terraform.io/docs/state/remote.html) that points to a Cloud Storage bucket. Remote state is a feature of [backends](https://www.terraform.io/docs/backends) and, in this tutorial, is configured in the `backend.tf` files—for example:

    terraform {
      backend "gcs" {
        bucket = "${var.tf_state_bucket}"
        prefix = "env/dev"
      }
    }

In the following steps, you create a Cloud Storage bucket and change a few files to point to your new bucket and your Google Cloud project.

1.  In Cloud Shell, create the Cloud Storage bucket:

        PROJECT_ID=$(gcloud config get-value project)
        gsutil mb gs://${PROJECT_ID}-tfstate

1.  Enable [Object Versioning](https://cloud.google.com/storage/docs/object-versioning) to keep the history of your deployments:

        gsutil versioning set on gs://${PROJECT_ID}-tfstate

Enabling Object Versioning increases [storage costs](https://cloud.google.com/storage/pricing), which you can mitigate by configuring
[Object Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle) to delete old state versions.

### Grant permissions to your Cloud Build service account

To allow the [Cloud Build service account](https://cloud.google.com/cloud-build/docs/securing-builds/set-service-account-permissions) to run Terraform scripts 
with the goal of managing Google Cloud resources, you need to grant it appropriate access to your project. The service account needs to be able to modify Cloud 
Run, Cloud Storage, and IAM policies.

1.  In Cloud Shell, retrieve the email address for your project's Cloud Build service account:

        CLOUDBUILD_SA="$(gcloud projects describe $PROJECT_ID --format 'value(projectNumber)')@cloudbuild.gserviceaccount.com"

1.  Grant the required access to your Cloud Build service account:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/iam.securityAdmin
        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/run.admin
        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/storage.admin
        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/editor
   
### Directly connect Cloud Build to your GitHub repository

To synchronize source changes in the GitHub repository to deployed Cloud Build instances, follow
[these instructions](https://cloud.google.com/solutions/managing-infrastructure-as-code#directly_connecting_cloud_build_to_your_github_repository) to connect 
Cloud Build to your GitHub repository. Make sure to replace `solutions-terraform-cloudbuild-gitops` with
`cloud-monitoring-notification-delivery-integration-sample-code`.

You should now have a Cloud Build trigger that builds and deploys the code when a source code change is pushed to the repository. See
[Creating a build trigger](https://cloud.google.com/cloud-build/docs/automating-builds/create-manage-triggers#build_trigger) for information on how to make sure
that the trigger’s build configuration is set to `./cloudbuild.yaml` and that the trigger event is set to **Push to branch**. On the `dev` project, the source
branch regular expression should be `^dev$`; on the `prod` project, the source branch regular expression should be `^prod$`.

### Grant permission to access Secret Manager

To allow the Cloud Run service to access secrets in Secret Manager, grant the Compute Engine default service account the Secret Manager Secret Accessor role:

    gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:[PROJECT_NUMBER]-compute@developer.gserviceaccount.com --role roles/secretmanager.secretAccessor

Replace `[PROJECT_NUMBER]` with the Cloud project number.

### Deploy the Philips Hue integration

1.  Store your Philips Hue bridge IP address as `philips_ip` and username as `philips_username` in
    [Secret Manager](https://cloud.google.com/secret-manager/docs/quickstart#create_and_access_a_secret_version).
1.  Check out the desired GitHub environment branch.
1.  Edit the `cloudbuild.yaml` configuration file to build a Philips Hue Docker image.

    Make sure that this line is set in the `build docker image` step: 
    
        args: ['build', '--build-arg', 'PROJECT_ID=$PROJECT_ID', '--tag', 'gcr.io/$PROJECT_ID/${_IMAGE_NAME}', './philips_hue_integration_example']
 
1.  Trigger a build:

    If there are any uncommitted changes for your branch, commit and push the changes to build and deploy the service.
    
    If no changes were made, manually trigger the build:
    
        cd ~/cloud-monitoring-notification-delivery-integration-sample-code
        gcloud builds submit . --config cloudbuild.yaml --substitutions BRANCH_NAME=branch

    Replace `branch` with the current environment branch.

The Cloud Run service should be up and running.

### Deploy the Jira integration

1.  Store your Jira server URL as `jira_url` and Jira project as `jira_project` in
    [Secret Manager](https://cloud.google.com/secret-manager/docs/quickstart#create_and_access_a_secret_version).
1.  Set up [Jira OAuth](https://developer.atlassian.com/server/jira/platform/oauth/) to be used to authenticate the Jira client in the Cloud Run service.
    Replace `[JIRA_URL]` with your Jira Server URL: 
 
        python3 jira_oauth_setup_script.py --gcp_project_id=$PROJECT_ID [JIRA_URL]
 
    This script prompts you to complete some steps manually.

1.  Check out the desired GitHub environment branch.
1.  Edit the `cloudbuild.yaml` configuration file to build a Jira Docker image.

    Make sure that this line is set in the `build docker image` step:

        args: ['build', '--build-arg', 'PROJECT_ID=$PROJECT_ID', '--tag', 'gcr.io/$PROJECT_ID/${_IMAGE_NAME}', './jira_integration_example']

1.  Trigger a build:

    If there are any uncommitted changes for your branch, commit and push the changes to build and deploy the service.
    
    If no changes were made, manually trigger the build:

        cd ~/cloud-monitoring-notification-delivery-integration-sample-code
        gcloud builds submit . --config cloudbuild.yaml --substitutions BRANCH_NAME=branch
 
    Replace `branch` with the current environment branch.

The Cloud Run service should be up and running.

### Configure policy notification channels to send alerts to Pub/Sub topic

To send notifications to the Pub/Sub topic called `tf-topic`, created by Terraform, do the following:

1. [Create a Pub/Sub notification channel](https://cloud.google.com/monitoring/support/notification-options#pubsub) that uses the topic `tf-topic`.
2. Add the Pub/Sub channel to an alerting policy by selecting **Pub/Sub** as the channel type and channel created in the prior step as the notification channel.

## Trying it out

If you have followed the instructions in this document, then all of the infrastructure is set up to deliver Cloud Monitoring alerts from these policies to a
Philips Hue light or Jira server.

## Cleaning up

If you created a new project for this tutorial, delete the project. If you used an existing project and wish to keep it without the changes added in this tutorial, delete resources created for the tutorial.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

Deleting a project has the following effects:

*  Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the 
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, such as an `appspot.com` URL, delete selected resources inside the project instead of deleting the whole project.

If you plan to explore multiple tutorials and quickstarts, reusing projects can help you avoid exceeding project quota limits.

To delete a project, do the following:

1.  In the Cloud Console, go to the **Manage resources** page.

    [Go to the **Manage resources** page](https://console.cloud.google.com/iam-admin/projects)
    
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete tutorial resources

1.  Delete the Cloud resources provisioned by Terraform:

        terraform destroy

1.  [Delete the Cloud Storage bucket](https://cloud.google.com/storage/docs/deleting-buckets) called `{PROJECT_ID}-tfstate`.
1.  Delete permissions that were granted to the Cloud Build service account:

        gcloud projects remove-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/iam.securityAdmin
        gcloud projects remove-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/run.admin
        gcloud projects remove-iam-policy-binding $PROJECT_ID --member serviceAccount:$CLOUDBUILD_SA --role roles/storage.admin

1.  Delete permissions to access Secret Manager:

        gcloud projects remove-iam-policy-binding $PROJECT_ID --member serviceAccount:[PROJECT_NUMBER]-compute@developer.gserviceaccount.com --role roles/secretmanager.secretAccessor

1.  Delete permission for the service account to publish to `tf-topic`:

        gcloud pubsub topics remove-iam-policy-binding \
        projects/[PROJECT_NUMBER]/topics/tf-topic --role=roles/pubsub.publisher \
        --member=serviceAccount:service-[PROJECT_NUMBER]@gcp-sa-monitoring-notification.iam.gserviceaccount.com

1.  [Delete the notification channel](https://cloud.google.com/monitoring/support/notification-options#editing_and_deleting_channels) that uses `tf-topic`.
1.  Delete the secrets stored in [Secret Manager](https://cloud.google.com/secret-manager/docs/managing-secrets#deleting_a_secret).
1.  [Delete your forked GitHub repository](https://docs.github.com/en/github/administering-a-repository/deleting-a-repository) `cloud-monitoring-notification-delivery-integration-sample-code`.
1.  Disconnect the GitHub repository from Cloud Build by
    [deleting the Cloud Build triggers](https://cloud.google.com/cloud-build/docs/automating-builds/create-manage-triggers#deleting_a_build_trigger).
1.  [Disable Google Cloud APIs](https://cloud.google.com/service-usage/docs/enable-disable#disabling).

## What's next

*   Learn more about the [Jira API](https://jira.readthedocs.io/en/master/api.html)
*   Learn more about the [Philips Hue API](https://developers.meethue.com/develop/hue-api/)
*   Learn more about [managing alerting policies](https://cloud.google.com/monitoring/alerts/using-alerting-ui)
*   Learn more about supported [notification channels](https://cloud.google.com/monitoring/support/notification-options#pubsub)
*   Learn more about [Pub/Sub architecture](https://cloud.google.com/pubsub/docs/overview) and how
    to [manage topics and subscriptions](https://cloud.google.com/pubsub/docs/admin)
