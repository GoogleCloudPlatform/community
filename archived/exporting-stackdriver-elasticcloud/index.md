---
title: Exporting Cloud Logging logs to Elastic Cloud
description: Learn how to send Cloud Logging events to Elastic Cloud for analysis.
author: twenny
tags: Stackdriver, logging, security, compliance
date_published: 2019-03-20
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial explains how to export Cloud Logging logs to the Elastic Cloud Elasticsearch SaaS platform to perform log 
analytics. Elastic Cloud is a SaaS offering, which saves time by not needing to build and manage the Elasticsearch 
infrastructure.

![Stackdriver to Elastic Cloud architecture](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/stackdriver_es_architecture.png)

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

New Google Cloud users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Configure Google Cloud resources

The high-level steps in this section:

1. Create a user-managed service account
1. Create a VM for Logstash
1. Create a Cloud Pub/Sub topic
1. Create a log sink and subscribe it to the Pub/Sub topic

## Enable APIs

Log in or sign up for [Google Cloud](https://cloud.google.com), then open
the [Cloud Console](https://console.cloud.google.com).

The examples in this document use the `gcloud` command-line interface. Google Cloud APIs must be enabled through the
[Services and APIs page](https://console.cloud.google.com/apis/dashboard) in the console before they can be used
with `gcloud`. To perform the steps in this tutorial, enable the following APIs: 

* Compute Engine
* Pub/Sub
* Identity and Access Management (IAM)
* Cloud Logging

![Enable Cloud APIs](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/enable_apis.png)

## Activate Cloud Shell

The Cloud Console provides an interactive shell that includes the `gcloud` command-line interface. At the top right corner of
the page, click the **Activate Cloud Shell** button.

![alt text](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/cloud_shell_icon.png)

## Create a service account

Google Cloud [best practices](https://cloud.google.com/vpc/docs/firewalls#service-accounts-vs-tags) suggest using a 
service account to configure security controls to a VM. A service account is useful for a VM to determine which other Google Cloud 
resources can be accessed by the VM and its applications, and which firewall rules should be applied to the VM.

While credentials can be created to be used by a service account, this step is not necessary when the service account is
attached to a VM running on Compute Engine. Google manages the keys, and applications can
[retrieve the credentials securely](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#authenticating_applications_using_service_account_credentials)
with the metadata service.

1.  Create a service account to attach to the VM:

        gcloud iam service-accounts create logstash \
            --display-name="Logstash to Stackdriver"

    **Expected response:**

        Created service account [logstash].
    
2.  Provide IAM permissions allowing the new service account to access Pub/Sub using the `pubsub.subscriber` role.

        gcloud projects add-iam-policy-binding scalesec-dev \
        --member serviceAccount:logstash@scalesec-dev.iam.gserviceaccount.com \
        --role roles/pubsub.subscriber

    **Excerpt of expected response:**

        Updated IAM policy for project [scalesec-dev].
        [...]
        - members:
          - serviceAccount:logstash@scalesec-dev.iam.gserviceaccount.com
          role: roles/pubsub.subscriber
        [...]
        etag: BwWEjM0909E=
        version: 1


## Create a Pub/Sub topic and subscription

1.  Create a Pub/Sub topic where Cloud Logging will send events to be picked up by Logstash:

        gcloud pubsub topics create stackdriver-topic

    **Expected response:**

        Created topic [projects/scalesec-dev/topics/stackdriver-topic].

    Next, create a subscription:

        gcloud pubsub subscriptions create logstash-sub --topic=stackdriver-topic --topic-project=scalesec-dev

    **Expected response:**

        Created subscription [projects/scalesec-dev/subscriptions/logstash-sub].

## Create a log sink

1.  Create a log sink to be used to export logs to the new Pub/Sub topic.

        gcloud logging sinks create logstash-sink pubsub.googleapis.com/projects/scalesec-dev/topics/stackdriver-topic \
        --log-filter='resource.type="project"'

    **Expected response:**  

        Created [https://logging.googleapis.com/v2/projects/scalesec-dev/sinks/logstash-sink].
        Please remember to grant `serviceAccount:p352005273005-058743@gcp-sa-logging.iam.gserviceaccount.com` Pub/Sub
        Publisher role to the topic.
        More information about sinks can be found at https://cloud.google.com/logging/docs/export/ 

    The filter specified above will produce events associated with changes to IAM, which is a typical area to be monitored
    closely. Cloud Logging supports monitoring activities for vpn_gateway and other resource types. See the
    [documentation](https://cloud.google.com/logging/docs/view/overview) for more filter ideas.

    The second part of the output is a reminder to verify that the service account used by Cloud Logging has permissions 
    to publish events to the Pub/Sub topic. The beta version of `gcloud` CLI supports permissions management for Pub/Sub. 

        gcloud beta pubsub topics add-iam-policy-binding stackdriver-topic \
        --member serviceAccount:p352005273005-776084@gcp-sa-logging.iam.gserviceaccount.com \
        --role roles/pubsub.publisher

    **Expected response:**

        Updated IAM policy for topic [stackdriver-topic].
        bindings:
        - members:
          - serviceAccount:p352005273005-776084@gcp-sa-logging.iam.gserviceaccount.com
          role: roles/pubsub.publisher
        etag: BwWEi9uEM1A=


## Create the Logstash VM

**Note:** Some system responses are omitted in this section for brevity.

1.  Create a VM to run `logstash` to pull logs from the Pub/Sub logging 
    sink and send them to ElasticSearch:

        gcloud compute --project=scalesec-dev instances create logstash \
        --zone=us-west1-a \
        --machine-type=n1-standard-1 \
        --subnet=default \
        --service-account=logstash@scalesec-dev.iam.gserviceaccount.com \
        --scopes="https://www.googleapis.com/auth/cloud-platform" \
        --image-family=ubuntu-1804-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=10GB \
        --boot-disk-type=pd-ssd \
        --boot-disk-device-name=logstash
  
    **Expected response:**  

        Created [https://www.googleapis.com/compute/beta/projects/scalesec-dev/zones/us-west1-a/instances/logstash].
        NAME      ZONE        MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
        logstash  us-west1-a  n1-standard-1               10.138.0.3   35.233.166.234  RUNNING

## Create Elastic Cloud deployment

1.  Go to https://cloud.elastic.co/login. A trial account provides suitable service to complete this tutorial.

    ![Sign up for Elastic Cloud](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/es_trial.png)

2.  Create an Elasticsearch deployment. This example is deployed on Google Cloud in us-west1. 

    ![Create an Elastic Cloud deployment](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/create_es_deployment.png)

3.  While the deployment is finishing up, make sure to capture the credentials and store them in a safe place. While
    the Cloud ID can be viewed from the deployment page, this is the only time the password for the elastic user is 
    available. Visit the **Security** page to reset the password if needed. When considering production environments, create
    new Elasticsearch credentials with tighter permissions and avoid using the `elastic` user. As
    [documented](https://www.elastic.co/guide/en/cloud-enterprise/current/ece-cloud-id.html): "On a production system, you should adapt 
    these examples by creating a user that can write to and access only the minimally required indices."

    ![Launching an Elastic Cloud deployment](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/es_deployment_launch.png)

4.  Obtain the URI of the Elasticsearch endpoint that has been provisioned. A link to this endpoint can be copied from the 
    **Deployments** page. This value will be needed to configure Logstash output plugin configuration.

    ![Copy the Elasticsearch URI](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/copy_es_uri.png)

    The next section provides steps to complete the setup to send events to the new Elasticsearch deployment.

## Configure the Logstash VM

1.  Compute Engine supports several [ways](https://cloud.google.com/compute/docs/instances/connecting-to-instance) to
    access your VM. You can use the `gcloud` command in Cloud Shell to leverage `oslogin` to connect to the `logstash` VM 
    via SSH, noting the zone from the VM creation step above.

        gcloud compute ssh logstash --zone us-west1-a

2.  Perform typical system updates and install OpenJDK:

        sudo apt-get update
        sudo apt-get -y upgrade
        sudo apt -y install openjdk-8-jre-headless
        echo "export JAVA_HOME=\"/usr/lib/jvm/java-8-openjdk-amd64\"" >> ~/.profile
        sudo reboot

    After a few moments, the VM will complete its reboot and can be accessed again via `gcloud`.

        gcloud compute ssh logstash --zone us-west1-a

## Install Logstash

1.  Install logstash from Elastic.

        wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
        echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
        sudo apt-get update
        sudo apt-get install logstash

1.  Install the Logstash Plugin for Pub/Sub. 

        cd /usr/share/logstash
        sudo -u root sudo -u logstash bin/logstash-plugin install logstash-input-google_pubsub

    **Expected response:**  

        Validating logstash-input-google_pubsub  
        Installing logstash-input-google_pubsub  
        Installation successful  

## Configure Logstash

Logstash comes with no default configuration. 

1.  Create a new file `/etc/logstash/conf.d/logstash.conf` with these contents, modifying values as needed:

        input
        {
            google_pubsub {
                project_id => "scalesec-dev"
                topic => "stackdriver-topic"
                subscription => "logstash-sub"
                include_metadata => true
                codec => "json"
            }
            # optional, but helpful to generate the ES index and test the plumbing
            heartbeat {
                interval => 10
                type => "heartbeat"
            }
        }
        filter {
            # don't modify logstash heartbeat events
            if [type] != "heartbeat" {
                mutate {
                    add_field => { "messageId" => "%{[@metadata][pubsub_message][messageId]}" }
                }
            }
        }
        output
        {
            stdout { codec => rubydebug }
            elasticsearch
            {
                hosts => ["https://c36297ebbc024cd4b29c98319dc8c38d.us-west1.gcp.cloud.es.io:9243"]
                user => "elastic"
                password => "NTmWdNJXkzMWL4kkIcIzY8O6"
                index => "logstash-%{+YYYY.MM.dd}"
            }
        }

## Start Logstash

1.  Start Logstash:

        sudo service logstash start

1.  Monitor the startup logs closely for issues:

        sudo tail -f /var/log/syslog

1.  Review log messages. It may take a few moments for events to begin flowing.

    Log messages like these indicate that Logstash is working internally:

        Jul 15 20:43:09 logstash logstash[2537]: {
        Jul 15 20:43:09 logstash logstash[2537]:           "type" => "heartbeat",
        Jul 15 20:43:09 logstash logstash[2537]:      "messageId" => "%{[@metadata][pubsub_message][messageId]}",
        Jul 15 20:43:09 logstash logstash[2537]:        "message" => "ok",
        Jul 15 20:43:09 logstash logstash[2537]:     "@timestamp" => 2018-07-15T20:43:08.367Z,
        Jul 15 20:43:09 logstash logstash[2537]:       "@version" => "1",
        Jul 15 20:43:09 logstash logstash[2537]:           "host" => "logstash"
        Jul 15 20:43:09 logstash logstash[2537]: }

    Log messages like these indicate that Logstash is pulling events from Cloud Pub/Sub. Actual message content will differ.

        Jul 17 20:58:13 logstash logstash[15198]:              "logName" => "projects/scalesec-dev/logs/cloud.googleapis.com%2Fipsec_events",
        Jul 17 20:58:13 logstash logstash[15198]:             "resource" => {
        Jul 17 20:58:13 logstash logstash[15198]:         "labels" => {
        Jul 17 20:58:13 logstash logstash[15198]:             "project_id" => "scalesec-dev",
        Jul 17 20:58:13 logstash logstash[15198]:                 "region" => "us-west1",
        Jul 17 20:58:13 logstash logstash[15198]:             "gateway_id" => "1810546051445508503"
        Jul 17 20:58:13 logstash logstash[15198]:         },
        Jul 17 20:58:13 logstash logstash[15198]:           "type" => "vpn_gateway"
        Jul 17 20:58:13 logstash logstash[15198]:     },
        Jul 17 20:58:13 logstash logstash[15198]:             "severity" => "DEBUG",
        Jul 17 20:58:13 logstash logstash[15198]:           "@timestamp" => 2018-07-17T20:58:12.918Z,
        Jul 17 20:58:13 logstash logstash[15198]:          "textPayload" => "sending packet: from 35.233.211.219[500] to 35.231.4.41[500] (49 bytes)",
        Jul 17 20:58:13 logstash logstash[15198]:             "insertId" => "1e8d5s7f6uc4ap",
        Jul 17 20:58:13 logstash logstash[15198]:            "timestamp" => "2018-07-17T20:58:08.401562594Z",
        Jul 17 20:58:13 logstash logstash[15198]:             "@version" => "1",
        Jul 17 20:58:13 logstash logstash[15198]:               "labels" => {
        Jul 17 20:58:13 logstash logstash[15198]:         "tunnel_id" => "1091689068647389715"
        Jul 17 20:58:13 logstash logstash[15198]:     },
        Jul 17 20:58:13 logstash logstash[15198]:            "messageId" => "146817684320772",
        Jul 17 20:58:13 logstash logstash[15198]:     "receiveTimestamp" => "2018-07-17T20:58:08.65636792Z"

## Configure Kibana

Kibana is a powerful graphical user interface that uses the underlying Elasticsearch data. This is the main console to 
monitor and triage security events and perform searches and investigations. 

1.  Return to the Elasticsearch deployment page and click the link to Kibana.

    ![Click to access the Kibana UI](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/kibana_url.png)

1.  Log in as the `elastic` user.

    ![Kibana login screen](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/kibana_login.png)

1.  Navigate to the **Management** page to set up index patterns for Kibana.

    ![Manage Kibana index patterns](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/kibana_index_patterns.png)

1.  Enter `logstash-*` for the index pattern.

    ![Configure logstash index pattern](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/define_index_pattern.png)

1.  Use `@timestamp` for the time field.

    ![Specify index timestamp](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/index_pattern_timestamp.png)

## Verify log flow

Return to the main Kibana dashboard (shown as **Discover** in the navigation menu). The Kibana dashboard should display
Cloud Logging events similar to those shown below:

![log flow](https://storage.googleapis.com/gcp-community/tutorials/exporting-stackdriver-elasticcloud/kibana_log_flow.png)
