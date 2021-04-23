---
title: Kitura on App Engine
description: Learn how to build an app with Swift and Kitura in the App Engine flexible environment.
author: asciimike
tags: App Engine, Swift, Kitura
date_published: 2017-03-21
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows a sample [Swift][swift] app built with [Kitura][kitura]
deployed to the App Engine flexible environment.

Kitura is "a high performance and simple to use web framework for
building modern Swift applications." It is [open source on GitHub][kitura-github].

This tutorial assumes basic familiarity with Swift programming.

[swift]: http://swift.org
[kitura]: https://kitura.io
[kitura-github]: https://github.com/IBM-Swift/Kitura

## Objectives

+ Create a Swift "Hello, world" app that uses the Kitura framework.
+ Deploy the app to the App Engine flexible environment.

## Costs

This tutorial uses billable components of Google Cloud, including App Engine flexible environment.

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Cloud Console][console].
1.  Enable billing for your project.
1.  Install the [Cloud SDK][cloud-sdk].

[console]: https://console.cloud.google.com/project
[cloud-sdk]: https://cloud.google.com/sdk/

## Handling dependencies

We'll use the [Swift Package Manager][spm] to manage our app's dependencies.

1.  Create a `Package.swift` file with the following contents:

        import PackageDescription
    
        let package = Package(
            name: "KituraGAE",
            targets: [
                Target(name: "KituraGAE", dependencies: [])
            ],
            dependencies: [
                .Package(url: "https://github.com/IBM-Swift/Kitura.git", majorVersion: 2, minor: 3),
            ]
        )

[spm]: https://github.com/apple/swift-package-manager

## Writing the server

1.  Create a `main.swift` file with the following contents:

        import Foundation
        import Kitura
    
        // All apps need a Router instance
        let router = Router()
    
        // Respond to App Engine health check requests
        // TODO: see #2
    
        // Basic GET request
        // TODO: see #3
    
        // Start server on 8080
        Kitura.addHTTPServer(onPort: 8080, with: router)
        Kitura.run()

1.  Create a route to handle App Engine health-check requests (per the [custom runtime docs][custom-runtime]):

        // Respond to App Engine health check requests
        router.all("/_ah/health") { request, response, _ in
             print("ALL - /_ah/health route handler...")
             try response.send("OK").end()
        }

1.  Create a route to handle `GET` requests to `/hello`:

         // Basic GET request
         router.get("/hello") { request, response, _ in
            print("GET - /hello route handler...")
            try response.status(.OK).send("Hello from Swift on App Engine flexible environment!").end()
         }

[custom-runtime]: https://cloud.google.com/appengine/docs/flexible/custom-runtimes/build#lifecycle_events

## Creating the `Dockerfile`

Since Swift doesn't have an officially supported App Engine runtime, we'll create our
own.

1.  Create a `Dockerfile` with the following contents:

         FROM ibmcom/swift-ubuntu:latest
         LABEL Description="Docker image for Swift + Kitura on App Engine flexible environment."
     
         # Expose default port for App Engine
         EXPOSE 8080
     
         # Copy sources
         RUN mkdir /root/KituraGAE
         ADD main.swift /root/KituraGAE
         ADD Package.swift /root/KituraGAE
     
         # Build the app
         RUN cd /root/KituraGAE && swift build
     
         # Run the app
         USER root
         CMD ["/root/KituraGAE/.build/debug/KituraGAE"]

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: custom
        env: flex

1.  Run the following command to deploy your app. It might take several minutes:

        gcloud app deploy

1.  Visit `http://[YOUR_PROJECT_ID].appspot.com/hello` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud project ID.

If all goes well, you should see "Hello from Swift on App Engine flexible environment!".
