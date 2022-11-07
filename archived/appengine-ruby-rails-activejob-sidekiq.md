---
title: Ruby on Rails background processing on App Engine with ActiveJob and Sidekiq
description: Learn how to run background jobs using Ruby on Rails ActiveJob.
author: chingor13,mohayat
tags: App Engine, Ruby, Ruby on Rails, ActiveJob, Sidekiq
date_published: 2017-06-08
---

Jeff Ching | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to create and configure a [Ruby on Rails](http://rubyonrails.org/) application to run
background processing jobs on the App Engine flexible environment using
[ActiveJob](http://guides.rubyonrails.org/active_job_basics.html) and [Sidekiq](http://sidekiq.org/).

## Objectives

* Create a background processing job.
* Deploy your application to the App Engine flexible environment.
* Verify that background jobs are running.

## Before you begin

You'll need the following:

* A Google Cloud project. You can use an existing project or create a new project.
* [Ruby 2.2.2+ installed](https://www.ruby-lang.org/en/documentation/installation/).
* A Rails 4.2+ application. Follow the
  ["Getting started with Rails" guide](http://guides.rubyonrails.org/getting_started.html) to get started.
* [Cloud SDK installed](https://cloud.google.com/sdk/downloads).
* A Redis instance running in your project. Follow [this guide](https://cloud.google.com/community/tutorials/setting-up-redis)
  to set up Redis on Compute Engine. This tutorial assumes the Redis instance is running in the *default*
  network so that the App Engine services can access it without restriction. Save or copy the password that you set for the Redis instance,
  which is used later in this tutorial.

## Costs

This tutorial uses billable components of Google Cloud including App Engine flexible environment.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. Google Cloud users might be eligible for a
[free trial](https://cloud.google.com/free-trial).

## Creating your background job

Starting with version 4.2, Ruby on Rails includes an abstraction layer around background job processing called
[ActiveJob](http://guides.rubyonrails.org/active_job_basics.html). This abstraction allows you to write the queuing
and execution logic independently of queue and job runner implementations.

Ruby on Rails provides command-line tools for generating templated skeletons for things such as database migrations,
controllers, and even background jobs.

You create a job named `HelloJob` that accepts a `name` argument and prints `"Hello #{name}"` to standard output.

1.  Use the Rails generator feature to create the `HelloJob` job:

        bin/rails generate job Hello

    Rails creates stub files from templates:

        invoke  test_unit
        create    test/jobs/hello_job_test.rb
        create  app/jobs/hello_job.rb
        create  app/jobs/application_job.rb

1.  Edit `app/jobs/hello_job.rb` with the following:

        class HelloJob < ApplicationJob
          queue_as :default

          def perform(name)
            # Do something later
            puts "Hello, #{name}"
          end
        end
   
## Create a test URL to queue the job

You create a controller named `HelloController` that provides an action called `say` that queues
the `HelloJob` job to run in the background.

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

1.  Add a `say` action to `HelloController` by adding the following to your `app/controllers/hello_controller.rb` file:

        class HelloController < ApplicationController
          def say
            HelloJob.perform_later(params[:name])
            render plain: 'OK'
          end
        end

    This action will queue our `HelloJob` with the provided request parameter `name`.

1.  Create a route to this action by adding the following to your `config/routes.rb` file:

        get '/hello/:name', to: 'hello#say'

    When you make an HTTP GET request to `/hello/Jeff`, the `HelloController` will handle the request using the `say`
    action with parameter `:name` as `"Jeff"`.

## Configuring your background worker to use Sidekiq

ActiveJob can be configured with various different background job runners. This tutorial uses Sidekiq, which
requires a Redis instance to manage the job queue.

1.  Add `sidekiq` gem to your `Gemfile`:

        bundle add sidekiq

1.  Configure ActiveJob to use Sidekiq as its queue adapter. In `config/application.rb`:

        class Application < Rails::Application
          # ...
          config.active_job.queue_adapter = :sidekiq
        end

## Deploying to App Engine flexible environment

For Sidekiq, the Redis connection configuration can be provided as an environment variable at run time. You
need to obtain the internal address and password of your Redis instance. In the Cloud Console, go to the
**[VM instances](https://console.cloud.google.com/compute/instances)** page and find the internal IP address of
your Compute Engine instance with Redis installed. This IP address and the password that you saved are be provided through environment variables
at deployment time to configure Sidekiq.

You create two App Engine services: one runs the web server and one runs worker processes. Both
services use the same application code. This configuration allows you to scale background worker instances independently
of your web instances at the cost of potentially using more resources. To pass the App Engine health checks and keep your background worker instance 
alive, you use the [sidekiq_alive](https://github.com/arturictus/sidekiq_alive) gem to enable the Sidekiq server to respond to each liveness and readiness 
request with a `200` HTTP status code.

1.  Add `sidekiq_alive` to your `Gemfile`:

        bundle add sidekiq_alive

1.  Create a `sidekiq_alive.rb` initializer. In `config/initializers`: 

        SidekiqAlive.setup do |config|
          # ==> Server port
          # Port to bind the server.
          config.port = 8080

          # ==> Server path
          # HTTP path to respond to.
          config.path = '/health_check'

          # ==> Rack server
          # Web server used to serve an HTTP response.
          config.server = 'puma'
        end

1.  Create an `app.yaml` file for deploying the web service to App Engine:

        runtime: ruby
        env: flex

        entrypoint: bundle exec rails server -p 8080

        env_variables:
          REDIS_PROVIDER: REDIS_URL
          REDIS_URL: redis://[REDIS_IP_ADDRESS]:6379
          REDIS_PASSWORD: [PASSWORD]
          SECRET_KEY_BASE: [SECRET_KEY]

    Replace `[REDIS_IP_ADDRESS]` and `[PASSWORD]` with the internal IP address of your Redis instance and its required password that you gave it,
    respectively. Replace `[SECRET_KEY]` with a secret key for Rails sessions.

1.  Create a `worker.yaml` file for deploying the worker service to App Engine:

        runtime: ruby
        env: flex
        service: worker

        entrypoint: bundle exec sidekiq

        env_variables:
          REDIS_PROVIDER: REDIS_URL
          REDIS_URL: redis://[REDIS_IP_ADDRESS]:6379
          REDIS_PASSWORD: [PASSWORD]
          SECRET_KEY_BASE: [SECRET_KEY]

        liveness_check: 
          path: '/health_check'

        readiness_check:
          path: '/health_check'

        # Optional scaling configuration
        manual_scaling:
          instances: 1

    Replace `[REDIS_IP_ADDRESS]` and `[PASSWORD]` with the internal IP address of your Redis instance and its required password that you gave it, respectively.
    Replace the `[SECRET_KEY]` with a secret key for Rails sessions.

    The `path` attribute for both the `liveness_check` and `readiness_check` sections has been set to the value of `config.path` in your `sidekiq_alive.rb` 
    initializer.

    As mentioned above, you can configure scaling for the worker service independent of the default (web) service.
    In the `manual_scaling` section, you have configured the worker service to start with one worker instance. For
    more information on scaling options, see
    [scaling configuration options in app.yaml](https://cloud.google.com/appengine/docs/flexible/ruby/configuring-your-app-with-app-yaml#services).
    If you choose an `automatic_scaling` option, be aware that scaling for the background processing is based off
    of CPU utilization, not queue size.

1.  Deploy both services to App Engine:

        gcloud app deploy app.yaml worker.yaml

## Verify that background queuing works

1.  In the Cloud Console, go to the
    **[App Engine services](https://console.cloud.google.com/appengine/services)** page. Locate the service that is
    running your background workers (if option A, it should be the *default* service, if option B, it should be
    the *worker* service). Click **Tools** > **Logs** for that service.

1.  In a separate window, navigate to your deployed Rails application:

        https://[YOUR_PROJECT_ID].appspot.com/hello/Jeff

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud project ID.

1.  Navigate back to the Logs dashboard. In the **Filter by label or text search** field, add `"Hello, Jeff"`
    and you should see a logging statement like the following if using foreman:

        13:13:52.000 worker.1 | Hello, Jeff

    Or, if using a second service:

        13:13:52.000 Hello, Jeff

Congratulations! You have successfully set up background job processing on App Engine with Sidekiq.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created on Google Cloud 
so you won't be billed for them in the future. The following sections describe how to delete or turn off these
resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

1. In the Cloud Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

### Deleting App Engine services

To delete an App Engine service:

1. In the Cloud Console, go to the **[App Engine Services](https://console.cloud.google.com/appengine/services)** page.
1. Click the checkbox next to the service you wish to delete.
1. Click **Delete** at the top of the page to delete the service.

If you are trying to delete the *default* service, you cannot. Instead, do the following:

1. Click on the number of versions which will navigate you to App Engine Versions page.
1. Select all the versions you wish to disable and click **Stop** at the top of the page. This will free
   all of the Google Compute Engine resources used for this App Engine service.

## Next steps

* Explore [the example code](https://github.com/chingor13/rails-background-jobs) used in this tutorial.
