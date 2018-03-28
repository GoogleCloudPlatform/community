---
title: Exposing ASP.NET Web API using .NET Core with Cloud Endpoints
description: Learn how to create a sample ASP.NET Web API service, deploy it to Google Cloud Platform (GCP) App Engine flexible environment, and use Cloud Endpoints for API management.
author: zeltser
tags: App Engine, Cloud Endpoints, .NET Core, ASP.NET, API Gateway, Web API, WebAPI, Deploy, API Management
date_published: 2017-04-01
---
# Create ASP.NET Web API using .NET Core with Cloud Endpoints

This tutorial shows how to create simple API using ASP.NET Core Web API,
deploy that API to App Engine Flexible Environment, then using Cloud Endpoints to expose and monitor the API.

## Step 1 - Setup your development environment

We are going to write code using Visual Studio Code. Therefore, you should install the following:

* [.NET Core 2.0.0 SDK](https://www.microsoft.com/net/core)
* [Visual Studio Code](https://code.visualstudio.com/)
* [OmniSharp C# extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode.csharp)

## Step 2 - Create ASP.NET Core Web API using VS Code

1. Open a command line prompt and run the following commands:

        mkdir ExposeAPIWithEndpointsCore
        cd ExposeAPIWithEndpointsCore
        dotnet new webapi

    This will create a template Web API project using .NET Core 2.0.

2. Open `ExposeAPIWithEndpointsCore` folder you created in VS Code. It will look like this:

    ![VS Code First Screen](./VSCodeEndpointsFirstScreen.png)
3. Click on *"YES"* for **"Required assets to build and debug are missing from ExposeAPIWithEndpointsCore. Add them?"**

4. Press `F5` to build the template project.

5. Navigate to [http://localhost:5000/api/values](http://localhost:5000/api/values) in your browser.
    This is the output you should expect: **[“value1”, “value2”].**

    Now we have a pre-built `"Values"` controller in our sample project that exposes 5 HTTP REST APIs. Now we need to add OpenAPI support.

    OpenAPI is a set of specifications that describe REST APIs. It’s a format that is both machine and human readable. Originally this set of specifications was called **Swagger** but it was later renamed to OpenAPI. You can [read more](https://swagger.io/blog/getting-started-with-swagger-i-what-is-swagger/) to understand the idea behind OpenAPI.
    We need it to deploy API specification to Google Endpoints later on. We have two options - either create OpenAPI specification manually, or [use Swashbuckle tool](https://github.com/domaindrivendev/Swashbuckle.AspNetCore) that will auto-generate the specifications for us based on API definition. Of cause, I prefer the second option. You will find it beneficial over time, as you make changes to the API. To add it, we need to add a few nuget packages: [Swashbuckle.AspNetCore](https://www.nuget.org/packages/swashbuckle.aspnetcore/) and [Swagger](https://www.nuget.org/packages/Swashbuckle/) and then configure Swagger in our service startup.

6. In VS Code terminal, type this:

        dotnet add package Swashbuckle.AspNetCore

7. Make changes in *Startup.cs*.

    7.1 In `"using"` section at the start of the document, add this:

        using Swashbuckle.AspNetCore.Swagger;

    7.2 In `ConfigureServices` method, add this:

        public void ConfigureServices(IServiceCollection services)
        {
            services.AddMvc();

            // Register the Swagger generator
            services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc(
                    "v1",
                    new Info { Title = "My API", Version = "v1" });
            });
        }

    7.3 In `"Configure"` method, add this:

        public void Configure(
            IApplicationBuilder app,
            IHostingEnvironment env)
        {
           if (env.IsDevelopment())
           {
               app.UseDeveloperExceptionPage();
           }

           // Enable middleware to serve generated Swagger as a JSON endpoint.
           app.UseSwagger();

           // Enable middleware to serve swagger-ui (HTML, JS, CSS, etc.), specifying the Swagger JSON endpoint.
           app.UseSwaggerUI(c =>
           {
               c.SwaggerEndpoint("/swagger/v1/swagger.json", "My API V1");
           });

           app.UseMvc();
        }

## Step 3 - Create OpenAPI specification for our API

1. Press `F5` in VS Code. Browse to [http://localhost:5000/swagger/v1/swagger.json](http://localhost:5000/swagger/v1/swagger.json)

    You should see Open API specification for our APIs in JSON format. However we will work with YAML representation of the same JSON. Even though Google Endpoints supports both json and YAML representations of OpenAPI, YAML is much more human friendly, so in case we will want to make manual changes to the specification, doing it in YAML file will be easier.

2. Copy the JSON content from the browser and paste it into [https://editor.swagger.io](https://editor.swagger.io). 
    You will be asked whether to translate JSON to YAML. Say `YES`. You will see this:
    ![Swagger Editor](./SwaggerYamlFromEditor.io.png)

3. Create a new file in VS Code under the main folder `ExposeApiWithEndpointsCore`. Name it `openapi.yaml` and paste the content of the generated YAML from https://editor.swagger.io.

    Now we are ready to deploy the API to Google Cloud Platform!

## Step 4 - Create a new GCP Project

1. [Create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project) at https://console.cloud.google.com

    We will create App Engine Flexible Environment and deploy our API to it from the command line. So now we need to make sure that Google Cloud SDK is pre-configured to work with the project we just created. 

2. Open Google Cloud SDK command line in elevated mode (Administrator), and type:

    2.1 Update SDK components to the latest

        gcloud components update

    2.2 Make sure that gcloud has permissions to work with our cloud project.

        gcloud auth login

    This will open a new browser window where we need to authenticate using our user account.

    2.3 Configure default project for all subsequent commands we will execute:

        gcloud config set project `YOUR_PROJECT_ID`

    2.4 Create [App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/) to which we will deploy our API. You can find the list of supported regions [here](https://cloud.google.com/appengine/docs/locations).

        gcloud app create --project --region=`YOUR_REGION`

    Congrats! We just finished with cloud setup! Now it's time to deploy the API specification and API implementation.

## Step 5 - Deploy API Specification to Google Endpoints

1. Open `openapi.yaml` that was created in step 3 in VS Code.

2. Add `host` declaration right before the `paths` section. The value should be `YOUR-PROJECT-ID.appspot.com` (replace `YOUR-PROJECT-ID` with your cloud project Id):
    <pre>
        swagger: '2.0'
        info:
        version: v1
        title: My API
        <b><i>host: YOUR-PROJECT-ID.appspot.com</i></b>
        paths:
          /api/Values:
        get:
            tags:
            - Values
            operationId: ApiValuesGet
    </pre>

    When you will deploy API specification to Google Endpoints, it will create a new Cloud Endpoints service configuration with the name equals to `host` value from our `OpenAPI yaml`. Each endpoints deployment assigns a unique `configuration_id` for versioning purposes. When we will deploy the service implementation to AppEngine Flexible environment in the next step, it will create a DNS entry in the format of `YOUR-PROJECT_ID.appspot.com`. We should use that FQDN to make incoming requests to our API.

3. In Google SDK command prompt, make sure you are in the folder that contains `openapi.yaml` that was created in step 3. Execute:

        gcloud endpoints services deploy openapi.yaml

    You should notice that the deployment shows a few warnings, such as `Operation does not require an API Key`. You can ignore these for now.

    So what has happened now? You just deployed API specification. This created a new Cloud Endpoints service configuration entry with the name that we specified in `“host”` field of `openapi.yaml`. This service entry is pre-configured to serve the API based on the specifications in yaml file. Now we want to ensure that all incoming API calls will be intercepted by Cloud Endpoints and then routed for execution to the service we deploy to AppEngine Flexible.

## Step 6 - Deploy API implementation to AppEngine Flexible

    Now you need to deploy API implementation. You also need to bind API specification we deployed earlier to API implementation instance, so that every incoming request passes through Cloud Endpoints service first, before it hits the deployment of API implementation.
    When deploying AppEngine Flexible service, you should specify Endpoints service name in the `app.yaml`. You should also set deployment rollout strategy to managed. By doing that, you instruct AppEngine Flexible to place an instance of Cloud Endpoints service in front of your API implementation. That instance is identified by service name and configuration id. By setting `rollout_strategy=managed` in `app.yaml`, we instruct the service to always use latest version of Cloud Endpoints service (the one that was deployed last).

1. In Google Cloud SDK shell type:

        gcloud endpoints configs list --service=`YOUR-PROJECT-ID`.appspot.com

    The output will show the `CONFIG_ID` and `SERVICE_NAME`.

2. Create `app.yaml` file in VS Code at `ExploreApiWithEndpointsCore` directory. The content of the file should be:

        Runtime: aspnetcore
        env: flex
        endpoints_api_service:
          name: [SERVICE_NAME]
          rollout_strategy: managed

    Replace `[SERVICE_NAME]` with corresponding value of previous command output.

    By creating `app.yaml` with `endpoints_api_service` section, we effectively created the binding that will ensure that every incoming request to our API (specification is detailed in configuration with config_id) that will hit `YOUR-PROJECT-ID.appspot.com` (“name”), will be routed to our service.
    Now you are almost ready to deploy API implementation into AppEngine Flex. In order to separate a project from its publish package in dotnet core, you should deploy the outcome of `dotnet publish` command. That output by default doesn’t contain `app.yaml` file we created earlier.

3. Edit `“ExposeAPIWithEndpointsCore.csproj”` in VSCore so it always copies `app.yaml` into the publish directory. Add this section before `</Project>` in `ExposeAPIWithEndpointsCore.csproj`:

        <!-- Copy the app.yaml on publish -->
        <ItemGroup>
           <None Include="app.yaml" CopyToOutputDirectory="Always" />
        </ItemGroup>
        </Project>

4. Deploy API implementation to AppEngine Flex.

        dotnet publish
        gcloud app deploy bin\debug\netcoreapp2.0\publish\app.yaml

5. Test that your APIs are exposed properly. Open `https://[YOUR-PROJECT-ID].appspot.com/api/Values` in any browser. If you get **["value1","value2"]** back, you are done!

## Congratulations!

You now have the API deployed and exposed via Cloud Endpoints! In order to prove that, go to [Endpoints](https://console.cloud.google.com/endpoints) page of Google Cloud Console. There you can inspect the requests graph. It should reflect the requests you made to test the API. Also you can see all the deployments of endpoints configuration.
![Monitoring API](./MonitorAPI.png)

## Summary

We created a basic ASP.NET Core Web API, deployed it to AppEngine Flex on Google Cloud Platform and configured Cloud Endpoints in front of our API, so all the incoming requests will be sent to Cloud Endpoints which in turn will route them to our API implementation. We haven’t implemented all the non functional requirements of exposing the API like security, throttling and monitoring yet. In this tutorial our API is exposed to everyone without any authentication.