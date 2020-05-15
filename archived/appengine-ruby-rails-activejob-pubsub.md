---
title: Ruby on Rails background processing on App Engine with ActiveJob and Cloud Pub/Sub
description: Learn how to run background jobs using Ruby on Rails ActiveJob.
author: chingor13
tags: App Engine, Ruby, Ruby on Rails, ActiveJob, PubSub
date_published: 2017-06-08
---

This tutorial shows how to create and configure a [Ruby on Rails](http://rubyonrails.org/) application to run
background processing jobs on App Engine flexible environment using
[ActiveJob](http://guides.rubyonrails.org/active_job_basics.html) and
[Cloud Pub/Sub](https://cloud.google.com/pubsub/).

## Objectives

* Create a background processing job
* Deploy your application to App Engine flexible environment
* Verify background jobs are running

## Before you begin

You'll need the following:

* A Google Cloud Platform (GCP) project. You can use an existing project or click the button to create a new project
* [Ruby 2.4.0+ installed](https://www.ruby-lang.org/en/documentation/installation/)
* A Rails 4.2+ application. Follow the
  [official "Getting Started with Rails" guide](http://guides.rubyonrails.org/getting_started.html) to get started.
* [Google Cloud SDK installed](https://cloud.google.com/sdk/downloads)

## Costs

This tutorial uses billable components of Cloud Platform including:

* App Engine flexible environment
* Cloud Pub/Sub

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. New GCP users might be eligible for a
[free trial](https://cloud.google.com/free-trial).

## Creating your background job

Starting with version 4.2, Ruby on Rails includes an abstraction layer around background job processing called
[ActiveJob](http://guides.rubyonrails.org/active_job_basics.html). This abstraction allows you to write the queuing
and execution logic independently of queue and job runner implementations.

Ruby on Rails provides command-line tools for generating templated skeletons for things such as database migrations,
controllers, and even background jobs.

You will create a job named `HelloJob` that will accept a `name` argument and print "Hello #{name}" to standard output.

1.  Use the Rails generator feature to create `HelloJob`:

        bin/rails generate job Hello

    Rails creates stub files from templates:

        invoke  test_unit
        create    test/jobs/hello_job_test.rb
        create  app/jobs/hello_job.rb
        create  app/jobs/application_job.rb

1.  Edit your `app/jobs/hello_job.rb` with the following:

        class HelloJob < ApplicationJob
          queue_as :default

          def perform(name)
            # Do something later
            puts "Hello, #{name}"
          end
        end

## Create a test URL to queue the job

You will create a controller named `HelloController` that will provide an action called `say` which will queue
our `HelloJob` to execute in the background.

1.  Use the Rails generator feature to create `HelloController`:

        bin/rails generate controller Hello

    Rails creates stub files from templates:

        create  app/controllers/hello_controller.rb
        invoke  erb
        create    app/views/hello
        invoke  test_unit
        create    test/controllers/hello_controller_test.rb
        invoke  helper
        create    app/helpers/hello_helper.rb
        invoke    test_unit
        invoke  assets
        invoke    coffee
        create      app/assets/javascripts/hello.coffee
        invoke    scss
        create      app/assets/stylesheets/hello.scss

1.  Add a `say` action to `HelloController`. Edit your `app/controllers/hello_controller.rb` with the following:

        class HelloController < ApplicationController
          def say
            HelloJob.perform_later(params[:name])
            render plain: 'OK'
          end
        end

   This action will queue our `HelloJob` with the provided request parameter `name`.

1.  Create a route to this action. In `config/routes.rb`, add:

        get '/hello/:name', to: 'hello#say'

    When you make an HTTP GET request to `/hello/Jeff`, the `HelloController` will handle the  request using the `say`
    action with parameter `:name` as "Jeff"

## Configuring your background worker to use Cloud Pub/Sub

ActiveJob can be configured with various different background job runners. This tutorial will cover
[ActiveJob::GoogleCloudPubsub](https://github.com/ursm/activejob-google_cloud_pubsub) which uses Cloud Pub/Sub
to manage the job queue.

1.  Add `activejob-google_cloud_pubsub` gem to your `Gemfile`:

        bundle add activejob-google_cloud_pubsub

1.  Configure ActiveJob to use GoogleCloudPubsub as its queue adapter. In `config/application.rb`:

        class Application < Rails::Application
          # ...
          config.active_job.queue_adapter = :google_cloud_pubsub
        end

## Deploying to App Engine flexible environment

### Option A: Shared worker and web application

For this option, the App Engine service will run both the web server and a worker process via a process manager called
[foreman](https://ddollar.github.io/foreman/). If you choose this method, App Engine will scale your web and worker
instances together.

1.  Add `foreman` gem to your `Gemfile`:

        bundle add foreman

1.  Create a `Procfile` at the root of your application:

        web: bundle exec rails server -p 8080
        worker: bundle exec activejob-google_cloud_pubsub-worker

1.  Create an `app.yaml` for deploying the application to App Engine:

        runtime: ruby
        env: flex

        entrypoint: bundle exec foreman start

        env_variables:
          SECRET_KEY_BASE: [SECRET_KEY]

    Be sure to replace the `[SECRET_KEY]` with a secret key for Rails sessions.

1.  Deploy to App Engine

        gcloud app deploy app.yaml

### Option B: Separate worker and web application

For this option, you are creating 2 App Engine services - one runs the web server and one runs worker processes. Both
services use the same application code. This configuration allows you to scale background worker instances independently
of your web instances at the cost of potentially using more resources.

1.  Create an `app.yaml` for deploying the web service to App Engine:

        runtime: ruby
        env: flex

        entrypoint: bundle exec rails server -p 8080

        env_variables:
          SECRET_KEY_BASE: [SECRET_KEY]

    Be sure to replace the `[SECRET_KEY]` with a secret key for Rails sessions.

1.  Create a `worker.yaml` for deploying the worker service to App Engine:

        runtime: ruby
        env: flex
        service: worker

        entrypoint: bundle exec activejob-google_cloud_pubsub-worker

        env_variables:
          SECRET_KEY_BASE: [SECRET_KEY]

        # Optional scaling configuration
        manual_scaling:
          instances: 1

    Be sure to replace the `[SECRET_KEY]` with a secret key for Rails sessions.

    Note that the health check is disabled here because the worker service is not running a web server and cannot
    respond to the health check ping.

    As mentioned above, you can configure scaling for the worker service independently of the default (web) service.
    In the `manual_scaling` section, you have configured the worker service to start with 1 worker instance. For
    more information on scaling options, see [scaling configuration options in app.yaml](https://cloud.google.com/appengine/docs/flexible/ruby/configuring-your-app-with-app-yaml#services).
    If you choose an `automatic_scaling` option, be aware that scaling for the background processing is based off
    of CPU utilization, not queue size.

1.  Deploy both services to App Engine

        gcloud app deploy app.yaml worker.yaml

## Verify your background queuing works

1. In the Cloud Platform Console, go to the
   **[App Engine Services](https://console.cloud.google.com/appengine/services)** page. Locate the service that is
   running your background workers (if option A, it should be the *default* service, if option B, it should be
   the *worker* service). Click Tools -> Logs for that service.

1. In a separate window, navigate to your deployed Rails application at:

        https://[YOUR_PROJECT_ID].appspot.com/hello/Jeff

   Be sure to replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

1. Navigate back to the Logs dashboard. In the **Filter by label or text search** field, add `"Hello, Jeff"`
   and you should see a logging statement like the following if using foreman:

        13:13:52.000 worker.1 | Hello, Jeff

    or if using a second service:

        13:13:52.000 Hello, Jeff

Congratulations, you have successfully set up background job processing on App Engine with Cloud Pub/Sub.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created on Google Cloud Platform
so you won't be billed for them in the future. The following sections describe how to delete or turn off these
resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Platform Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in
the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID,
such as an appspot.com URL, remain available.

### Deleting App Engine services

To delete an App Engine service:

1. In the Cloud Platform Console, go to the **[App Engine Services](https://console.cloud.google.com/appengine/services)** page.
1. Click the checkbox next to the service you wish to delete.
1. Click **Delete** at the top of the page to delete the service.

If you are trying to delete the *default* service, you cannot. Instead:

1. Click on the number of versions which will navigate you to the App Engine Versions page.
1. Select all the versions you wish to disable and click **Stop** at the top of the page. This will free
   all of the Google Compute Engine resources used for this App Engine service.

## Next steps

* Explore [the example code](https://github.com/chingor13/rails-background-jobs) used in this tutorial.
