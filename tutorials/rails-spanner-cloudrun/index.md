---
title: Deploy a Ruby on Rails application on Cloud Run with Cloud Spanner
description: Learn how to deploy a Ruby on Rails application on Cloud Run using Cloud Spanner as the backend database.
author: xiangshen-dk
tags: ruby, rails, activerecord, cloud spanner, cloud run
date_published: 2021-09-24
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to build and deploy a [Rails sample application](https://guides.rubyonrails.org/getting_started.html) to Cloud Run. The application uses Cloud Spanner for the backend database and accesses it through the [ActiveRecord Spanner Adapter](https://github.com/googleapis/ruby-spanner-activerecord).

## Objectives 

+   Build and deploy a Rails application on Cloud Run.
+   Use Cloud Spanner as the backend database
+   Access the database using Active Record

## Costs

This tutorial uses billable components of Google Cloud, including the following:

+   [Cloud Spanner](https://cloud.google.com/spanner/pricing)
+   [Cloud Run](https://cloud.google.com/run/pricing)

To generate a cost estimate based on your projected usage, use the
[pricing calculator](https://cloud.google.com/products/calculator).

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient 
    permissions to use the services listed above.

This tutorial uses [gcloud](https://cloud.google.com/sdk/gcloud) and [pack](https://buildpacks.io/docs/tools/pack/) command-line tools. 
Because [Cloud Shell](https://cloud.google.com/shell) includes these packages, we recommend that you run the commands in this tutorial in Cloud Shell, so that 
you don't need to install these packages locally.  

## Prepare your environment

### Set common variables  

You need to define several variables that control where elements of the infrastructure are deployed.

1.  In Cloud Shell, set the region, zone, and project ID:

        REGION=us-central1
        ZONE=${REGION}-b
        PROJECT_ID=[YOUR_PROJECT_ID]
   
    Replace `[YOUR_PROJECT_ID]` with your project ID. This tutorial uses the region `us-central1`. If you want to change the region, check that the zone 
    values are appropriate for the region that you specify.
   
1.  Enable all necessary services:

        gcloud services enable run.googleapis.com
        gcloud services enable spanner.googleapis.com
        gcloud services enable cloudbuild.googleapis.com
        gcloud services enable artifactregistry.googleapis.com
        gcloud services enable compute.googleapis.com

1.  Set the zone and project ID so that you don't have to specify these values in subsequent commands:

        gcloud config set project ${PROJECT_ID}
        gcloud config set compute/zone ${ZONE}
        gcloud config set run/region ${REGION}

## Create a Spanner instance
This step will create a Cloud Spanner instance. 

1. This tutorial will use a one-node instance in `regional-us-central1`.
You can choose a region close to you:
    ```shell
    gcloud spanner instances create test-instance --config=regional-us-central1 \
      --description="Rails Demo Instance" --nodes=1
    ```
1. Verify the instance has been created:
    ```shell
    gcloud spanner instances list
    ```
    You should see output like the following:
    ```
    NAME: test-instance
    DISPLAY_NAME: Rails Demo Instance
    CONFIG: regional-us-central1
    NODE_COUNT: 1
    STATE: READY
    ```
1. Set the default instance:
    ```shell
    gcloud config set spanner/instance test-instance
    ```

Read the [Cloud Spanner setup guide](https://cloud.google.com/spanner/docs/getting-started/set-up) for more details.

## Create a Rails project

If you don't have Ruby and Rails installed, please follow the steps in the following links to install them:

- [Installing Ruby](https://www.ruby-lang.org/en/documentation/installation/)
- [Installing Rails](https://guides.rubyonrails.org/getting_started.html#creating-a-new-rails-project-installing-rails)

If you are not familiar with Active Record, you can read more about it on [Ruby on Rails Guides](https://guides.rubyonrails.org/)

1. Verify the Ruby and Rails versions:
    ```shell
    ruby --version
    rails --version
    ```
    The versions should be Ruby 2.6 or higher and Rails 6.0 or higher.
1. Create a new Rails project. This step may take a few minutes if you run it in a Cloud Shell:

    ```shell
    rails new blog
    ```
1. The `blog` directory will have a number of generated files and folders that make up the structure of a Rails application. You can list them:
    ```shell
    cd blog
    ls -l
    ```
1. Starting up the web server and make sure the sample application works:
    ```shell
    bin/rails server
    ```
    After the server starts, open your browser and navigate to [http://localhost:3000](http://localhost:3000). You should see the default Rails page with the sentence: __Yay! You're on Rails!__
    Note: if you are using Cloud Shell, you can change the `Web Preview` port to `3000` and view the result. 

### Create a service account

1. Create a service account:
    ```shell
    gcloud iam service-accounts create activerecord-spanner
    ```
1. Grant an IAM role to access Cloud Spanner:
    ```shell
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:activerecord-spanner@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseAdmin"
    ```
    Here the role `roles/spanner.databaseAdmin` is granted to the service account. If you want to restrict the permissions further, you can choose to create a custom role with proper permissions.
1. Create a key file and download it:
    ```shell
    gcloud iam service-accounts keys create activerecord-spanner-key.json \
    --iam-account=activerecord-spanner@${PROJECT_ID}.iam.gserviceaccount.com
    ```
    This tutorial uses the key file to access Cloud Spanner. For services such as Compute Engine, Cloud Run, or Cloud Functions, you can associate the service account to the instance and avoid using the key file.
1. From the previous step, a key file should be created and downloaded. You can run the following command to view its content:
    ```shell
    cat activerecord-spanner-key.json
    ```

### Use Cloud Spanner adapter in Gemfile
1. Edit the Gemfile file of the `blog` app and add the `activerecord-spanner-adapter` gem:
    ```ruby
    gem 'activerecord-spanner-adapter'
    ```
1. Install gems:

    ```shell
    bundle install
    ```

### Update database.yml to use Cloud Spanner.
After the Cloud Spanner instance is running, you'll need a few variables:
* Cloud project id
* Cloud Spanner instance id, such as `test-instance`
* Database name, such as `blog_dev`
* Credential: Credential key file path or export `GOOGLE_CLOUD_KEYFILE`environment variable.

Edit the file `config/database.yml` and make the section `DATABASES` into the following:

```yml
default: &default
  adapter: "spanner"
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 10 } %>
  project: [PROJECT_ID]
  instance: test-instance

development:
  <<: *default
  database: blog_dev
  credentials: activerecord-spanner-key.json

test:
  <<: *default
  database: blog_test
  credentials: activerecord-spanner-key.json

production:
  <<: *default
  database: blog
```

Replace `[PROJECT_ID]` with the project id you are currently using.

### Create database
1. You now can run the following command to create the database:
    ```shell
    bin/rails db:create
    ```
1. You should see output like the following:
    ```
    Created database 'blog_dev'
    ```
### Generate a Model and apply the migration
1. Use the model generato to define a model:
    ```shell
    bin/rails generate model Article title:string body:text
    ```
1. Apply the migration:
    ```shell
    bin/rails db:migrate
    ```
    The command takes a while to complete. When it's done, you will have an output like the following:
    ```
    $ bin/rails db:migrate
    == 20210926214423 CreateArticles: migrating ===================================
    -- create_table(:articles)
       -> 23.1182s
    == 0210926214423 CreateArticles: migrated (23.1183s) ==========================
    ```

### Use the CLI to interact with the database
1. Run the following command to start `irb`:
    ```shell
    bin/rails console
    ```
1. At the prompt, initialize a new `Article` object:
    ```ruby
    article = Article.new(title: "Hello Rails", body: "I am on Rails!")
    ```
1. Run the following command to save the object to the database:
    ```ruby
    article.save
    ```
1. Review the object and you can see the field `id`, `created_at`, and `updated_at` have been set:
    ```ruby
    article
    ```
    Sample output:
    ```
    => #<Article id: 2089131394272333747, title: "Hello Rails", body: "I am on Rails!", created_at: "2021-09-26 21:48:08.676097375 +0000", updated_at: "2021-09-26 21:48:08.676097375 +0000"
    ```
1. You can find `Article.find(id)` or `Article.all` to fetch data from the database. For example:
    ```ruby
    irb(main):007:0> Article.find(2089131394272333747)
    Article Load (25.8ms)  SELECT `articles`.* FROM `articles` WHERE `articles`.`id` = @p1 LIMIT @p2
    => #<Article id: 2089131394272333747, title: "Hello Rails", body: "I am on Rails!", created_at: "2021-09-26 21:48:08.676097375 +0000", updated_at: "2021-09-26 21:48:08.676097375 +0000">

    irb(main):008:0> Article.all
    Article Load (28.6ms)  SELECT `articles`.* FROM `articles` /* loading for inspect */ LIMIT @p1
    => #<ActiveRecord::Relation [#<Article id: 2089131394272333747, title: "Hello Rails", body: "I am on Rails!", created_at: "2021-09-26 21:48:08.676097375 +0000", updated_at: "2021-09-26 21:48:08.676097375 +0000">]>
    ```
1. You can type `exit` to exit the console.
### Update the app to show a list of records
1. Use the controller generator to create a controller:
    ```shell
    bin/rails generate controller Articles index
    ```
1. Open the file `app/controllers/articles_controller.rb`, and change the `index` action to fetch all articles from the database:
    ```ruby
    class ArticlesController < ApplicationController
      def index
        @articles = Article.all
      end
    end
    ```
1. Open `app/views/articles/index.html.erb`, and update the file as the following:
    ```html
    <h1>Articles</h1>
    <ul>
      <% @articles.each do |article| %>
        <li>
          <%= article.title %>
        </li>
      <% end %>
    </ul>
    ```
1. Run your server again
    ```shell
    bin/rails s
    ```
1. In your browser, navigate to the URL [http://localhost:3000/articles/index](http://localhost:3000/articles/index). And you will see the `Hello Rails` record you entered previously. If you use the `Web Prview` from Cloud Shell, you need to update the URL similart to: https://xxxx.cloudshell.dev/`articles/index`.
1. [Optional] you can follow the rest of the steps in the [Getting Started with Rails](https://guides.rubyonrails.org/getting_started.html) guide.

## Deploy to Cloud Run

In this tutorial, you will deploy a development version of the Rails app to Cloud Run. You can read [Running Rails on the Cloud Run environment](https://cloud.google.com/ruby/rails/run) for more details, including deploying to a production environment and using a different Ruby version.

### Create a Dockerfile

```dockerfile
FROM ruby:2.7-buster

RUN (curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | gpg --dearmor | apt-key add -) && \
    echo "deb https://deb.nodesource.com/node_14.x buster main"      > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs lsb-release

RUN (curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -) && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update && apt-get install -y yarn

WORKDIR /app

COPY Gemfile Gemfile.lock ./

RUN gem install bundler && \
    bundle config set --local deployment 'true' && \
    bundle install

COPY . /app

ENV RAILS_ENV=development
ENV RAILS_SERVE_STATIC_FILES=true
ENV RAILS_LOG_TO_STDOUT=true
RUN bundle exec rake assets:precompile

EXPOSE 8080
CMD ["bin/rails", "server", "-b", "0.0.0.0", "-p", "8080"]
```

### Whitelist the domain

For Rails 6.x, you need to whitelist the domain to allow users to access the application in Cloud Run. For example, add the following line to `config/environments/development.rb`

    config.hosts << '.run.app'

### Deploy from source

    gcloud run deploy rails-sample --allow-unauthenticated \
        --timeout 20m \
        --source .

When building the container image, you can open the Cloud Build logging page to view the progress. It takes a few minutes to build and deploy the application.

Once it's finished, you should see a similar output like the following:

```
......
Building using Dockerfile and deploying container to Cloud Run service [rails-sample] in project [xxx-xxx] region [us-central1]
OK Building and deploying new service... Done.                                                           
  OK Uploading sources...
  OK Building Container... Logs are available at [https://console.cloud.google.com/cloud-build/builds/e798d84d-1581-42e9-bea9-f6e949b25dc1?project=346435283219].
  OK Creating Revision...                                                                 
  OK Routing traffic...
  OK Setting IAM Policy...
Done.
Service [rails-sample] revision [rails-sample-00001-fol] has been deployed and is serving 100 percent of traffic.
Service URL: https://rails-sample-cmvcdiktlq-uc.a.run.app
```
### Test the deployment

Open your brower using the `Service URL` from the previous step and you should see the Rails default page. The URL can also be found from the Cloud Run service page.

Appeneding `/articles/index` to the service URL, for example `https://rails-sample-cmvcdiktlq-uc.a.run.app/articles/index`, and update the page. You should see the same result as your local environment.


## Clean up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the resources you created. You can either 
delete the entire project or delete individual resources.

Deleting a project has the following effects:

* Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, delete selected resources inside the project instead of deleting the whole project.

If you plan to explore multiple tutorials, reusing projects can help you to avoid exceeding project quota limits.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial. 

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).  
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the resources

If you don't want to delete the project, you can delete the provisioned resources:

    gcloud iam service-accounts delete \
    activerecord-spanner@${PROJECT_ID}.iam.gserviceaccount.com

    gcloud spanner instances delete test-instance
    gcloud run services delete rails-sample

## What's next

+   Learn about [running Rails on Cloud Run with Cloud SQL](https://cloud.google.com/ruby/rails/run).
+   Learn about [ActiveRecord Cloud Spanner Adapter](https://github.com/googleapis/ruby-spanner-activerecord).
+   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).