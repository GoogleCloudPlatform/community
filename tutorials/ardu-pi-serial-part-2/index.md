---
title: Locally connected microcontrollers and real-time analytics (part 2 of 2)
description: Learn how to process, store, and analyze streaming sensor data in real time.
author: markku,varundhussa
tags: IoT, Internet of Things, Dataflow, BigQuery, Data Studio, PubSub, Cloud Datalab
date_published: 2019-03-20
---

Varun Dhussa | Solutions Architect | Google Cloud Platform

Markku Lepisto | Solutions Architect | Google Cloud Platform

This two-part tutorial demonstrates how to control an [Arduino Microcontroller](https://www.arduino.cc/) with a
[Raspberry Pi](https://www.raspberrypi.org/), connect the devices to [Cloud IoT Core](https://cloud.google.com/iot-core/),
post sensor data from the devices, and analyze the data in real time.
[Part 1](https://cloud.google.com/community/tutorials/ardu-pi-serial-part-1) of the tutorial created a *hybrid*
device, combining the strengths of a Linux-based microprocessor with internet connectivity and TLS stack, together with a 
constrained microcontroller for analog I/O.

## Part 2 objectives

- Process sensor data from Cloud Pub/Sub using Cloud Dataflow.
- Store processed sensor data in BigQuery.
- Create a report dashboard using Google Data Studio.
- Create a notebook on Cloud Datalab.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/architecture.png)

## Before you begin

This tutorial assumes that you already have a [Google Cloud Platform (GCP)](https://console.cloud.google.com/freetrial) 
account set up and have [Part 1](https://cloud.google.com/community/tutorials/ardu-pi-serial-part-1) of the tutorial 
working.

## Costs

This tutorial uses billable components of GCP, including the following:

- Cloud IoT Core
- Cloud Pub/Sub
- Cloud Dataflow
- BigQuery
- Cloud Datalab

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), 
but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on
your projected production usage.

## Enable Cloud Dataflow for your project

Perform all of the steps in the "Before you begin" section of the
[Cloud Dataflow Quickstart](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python)—through creating a Cloud 
Storage bucket—on your local development environment (e.g., laptop).

## Enable BigQuery for your project

Perform all of the steps in the "Before you begin" section of the
[BigQuery Quickstart](https://cloud.google.com/bigquery/docs/quickstarts/quickstart-web-ui).

## Install environment dependencies and the Google Cloud SDK

1.  Clone the source repository:

        $ git clone https://github.com/GoogleCloudPlatform/community.git

2.  Change to the directory for this tutorial:

        $ cd community/tutorials/ardu-pi-serial-part-2
    
3.  Create and activate the virtual environment:

        $ virtualenv my_virtual_env
        $ . ./my_virtual_env/bin/activate
        $ pip install -r beam-requirements.txt

4.  Follow the steps in [this guide](https://cloud.google.com/sdk/install) to install the Cloud SDK.

## Create a BigQuery dataset

[BigQuery](https://cloud.google.com/bigquery/) is Google's fully managed serverless and highly scalable enterprise data
warehouse solution.

A BigQuery [dataset](https://cloud.google.com/bigquery/docs/datasets-intro) contains tables and views in a specified single 
region or a geography containing multiple regions. Follow the
[instructions](https://cloud.google.com/bigquery/docs/datasets) to create a dataset in your project. The dataset location 
can only be specified while creating it. More details are available
[here](https://cloud.google.com/bigquery/docs/locations).

## Start the Cloud Dataflow job

[Cloud Dataflow](https://cloud.google.com/dataflow/) is a fully managed service for transforming and enriching data in
stream (real-time) and batch (historical) modes with equal reliability and expressiveness using the
[Apache Beam SDK](https://beam.apache.org/). 

Select your preferred Cloud Dataflow [service region](https://cloud.google.com/dataflow/docs/concepts/regional-endpoints).

Run the command below to start the Apache Beam pipeline on the Cloud Dataflow runner.

    $ python -m beam-solarwind --project [project_name] \
    --topic [pub_sub_topic_name (e.g., projects/my-project/topics/my-topic)] \
    --temp_location gs://[cloud_storage_bucket]/tmp \
    --setup_file ./setup.py \
    --region [your_preferred_region] \
    --runner DataflowRunner \
    --output "[bigquery_table_dataset].[table_name]" \
    --output_avg "[bigquery_average_table_dataset].[table_avg]" 

Go to the [Cloud Dataflow](https://console.cloud.google.com/dataflow) interface in the GCP Console and select your 
newly created Cloud Dataflow job to see your pipeline.

The following diagram shows an example Cloud Dataflow pipeline:

![DF job](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/df-job.png)

The first part of the Cloud Dataflow job sets up the pipeline options with the required parameters passed through the 
command-line parameters, as shown above. The `streaming mode` option is also enabled. To allow access to the modules 
available in the main session, the `save_main_session` flag is set. After this, the beam pipeline object is created.

    args, pipeline_args = parser.parse_known_args(argv)
    options = PipelineOptions(pipeline_args)
    options.view_as(SetupOptions).save_main_session = True
    options.view_as(StandardOptions).streaming = True
    p = beam.Pipeline(options=options)

The first two steps of the Cloud Dataflow pipeline read incoming events from Cloud Pub/Sub and then parse the JSON text:

    records = (p | 'Read from PubSub' >> beam.io.ReadFromPubSub(
        topic=args.topic) | 'Parse JSON to Dict' >> beam.Map(
            json.loads))

There are two branches at the next step. The one on the right in the figure above writes the incoming stream of events to 
the raw BigQuery table. The table is created if it does not exist.

    # Write to the raw table
    records | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
        args.output,
        schema=Schema.get_warehouse_schema(),
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

The one on the left aggregates the events and writes them to the BigQuery average table.

1.  Use the timestamp in the event object and emit it with the object. This is then used to create a sliding window of 300
    seconds that starts every 30 seconds.

        records | 'Add timestamp' >> beam.ParDo(AddTimestampToDict()) |
             'Window' >> beam.WindowInto(beam.window.SlidingWindows(
                 300, 60, offset=0))
                 
2.  At the next stage, the record is emitted as a `key-value` tuple, in which the `clientid` is the key and the object is 
    the value.

        'Dict to KeyValue' >> beam.ParDo(AddKeyToDict())
    
3.  The elements are grouped by the clientid key, and the averages of all the metrics (temperature, pressure, etc.) are 
    calculated.

        'Group by Key' >> beam.GroupByKey() |
        'Average' >> beam.ParDo(CountAverages())

4.  The calculated average values are written to the BigQuery average table. The table is created if it does not exist.

        'Write Avg to BigQuery' >> beam.io.WriteToBigQuery(
             args.output_avg,
             schema=Schema.get_avg_schema(),
             create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
             write_disposition=BigQueryDisposition.WRITE_APPEND))

## View results in BigQuery

1.  Ensure that the client from [Part 1](https://cloud.google.com/community/tutorials/ardu-pi-serial-part-1) is running and 
    posting data to Cloud Pub/Sub through Cloud IoT Core.
2.  Go to the [BigQuery UI](https://console.cloud.google.com/bigquery) in the GCP Console.
3.  In the BigQuery menu, select your project `my_project_id`.
4.  Select the dataset `my_dataset`.
5.  Select the table `my_table`:
    1.  View the table schema.
    2.  See table details.
6.  Run the following queries to see the latest data:
    1.  Select the latest 20 records from the raw table:

            select * from [my_dataset].[my_table]
            order by timestamp DESC
            limit 20;
            
    2.  The average table adds a single row for each time window. Run the query below to select the latest 20 records.

            select * from [my_dataset].[my_avg_table]
            order by timestamp DESC
            limit 20;

**BigQuery table schema:**

![bq-schema](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/bq-schema.jpg)

**BigQuery table preview:**
![bq data](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/bq-data.jpg)

## Create a Data Studio report

Data Studio is a managed tool that allows creation and sharing of dashboards and reports.

1.  Go to the [Data Studio interface](https://datastudio.google.com).
2.  Click the **+** button to create a new blank report.
3.  Add a new Data Source:

    ![datasource](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/select_fields.png)

    1.  Click the **+ Create New Data Source** button
    2.  Select the **BigQuery by Google** connector
    3.  Select the BigQuery project `my_project_id`, dataset `my_dataset`, and table `my_table`, and then click **Connect**.
    4.  All the schema fields (clientid, temperature, pressure, etc.) would be auto-selected. 
    5.  Click **Add to report** and confirm by clicking the button in the popup.
4.  Create a new chart:

    ![addchart](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/gcreate.png)

    1.  Click **Add a Chart** in the menu bar.
    2.  Select a line chart.
    3.  Select Date and Time range dimensions as the timestamp column.
    4.  Select the `clientid` field as the breakdown dimension.
    5.  Select a metric (e.g., temperature) and aggregation (e.g., AVG).
    6.  Add a Text Box and label the chart.
    7.  Repeat the steps above for additional metrics.

**Data Studio report:**
![dsreport](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-2/ds-report.jpg)

## Create a Cloud Datalab notebook

Cloud Datalab is an interactive tool for data exploration that is built on [Jupyter](https://jupyter.org/).
The Jupyter Notebook is an open-source web application that allows you to create and share documents that contain live code,
equations, visualizations, and narrative text.

1.  Go to the [Cloud Datalab quickstart](https://cloud.google.com/datalab/docs/quickstart) and perform all of the steps in
    the "Before you begin" section.
2.  Go to the [notebooks page](http://localhost:8081/notebooks/datalab/notebooks/).
3.  Click the **Upload** button to add `community/tutorials/ardu-pi-serial-part2/solarwindreport.ipynb` to Cloud Datalab.
4.  Click the notebook to open and edit it.
    1.  Set the project ID (e.g., `my_project_id`).
    2.  Set the dataset name (e.g., `my_dataset`).
    3.  Set the raw table name (e.g., `my_table`).
    4.  Set the average table name (e.g., `my_avg_table`).
    5.  Set the location (e.g., `my_location`).
        **Important**: The [location](https://cloud.google.com/bigquery/docs/locations) must match that of the datasets
        referenced in the query.
    6.  Set the client id (e.g., `my_client_name`).
5.  From the **Kernel** menu in the menu bar, select **python3**.
6.  Click **Run** in the menu bar to execute the notebook.

## Clean up

1.  [Clean up](https://cloud.google.com/datalab/docs/quickstart#clean-up) the Cloud Datalab environment.
2.  Delete the Data Studio report:
    1.  Go to the [Data Studio interface](https://datastudio.google.com).
    2.  In the menu section, click the three-dot menu next to the report name.
    3.  Select **Remove**.
3.  Stop the [Cloud Dataflow](https://cloud.google.com/dataflow/docs/guides/stopping-a-pipeline) job.
4.  Delete the Cloud Storage bucket:

        $ gsutil rm -r gs://[cloud_storage_bucket]
  
5.  Delete the [BigQuery dataset](https://cloud.google.com/bigquery/docs/managing-datasets#deleting_a_dataset):

        $ bq rm -r [my_dataset]
        rm: remove dataset '[my_project_id]:[my_dataset]'? (y/N) y

6.  To delete a project, do the following:
    1.  In the GCP Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
    2.  In the project list, select the project you want to delete and click **Delete project**.
    3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

    ![deleting the project](https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png)

## What's next

* Check out the new [tutorial](https://cloud.google.com/community/tutorials/sigfox-gw) on using the
  Sigfox [Sens'it Discovery V3](https://www.sensit.io/) device with this integration and learning how to encode and decode 
  its binary data and configuration payloads, as well as store the data in real time in BigQuery.
* Learn more about [IoT on GCP](https://cloud.google.com/solutions/iot/).
* Learn more about [Big data analytics on GCP](https://cloud.google.com/solutions/big-data/), to turn your
  IoT data into actionable insights.
* Try out other GCP features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
