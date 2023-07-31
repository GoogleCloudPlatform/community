---
title: Perfect on App Engine
description: Learn how to build an app with Swift and Perfect in the App Engine flexible environment.
author: asciimike
tags: App Engine, Swift, Perfect
date_published: 2017-03-21
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows a sample [Swift][swift] app built with [Perfect][perfect]
deployed to the App Engine flexible environment.

Perfect is "a complete and powerful toolbox, framework, and application server
for Linux, iOS, and macOS (OS X)." It is [open source on GitHub][perfect-github].

This tutorial assumes basic familiarity with Swift programming.

[swift]: http://swift.org
[perfect]: https://perfect.org
[perfect-github]: https://github.com/PerfectlySoft/Perfect

## Objectives

+ Create a Swift "Hello, world" app that uses the Perfect framework.
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

[console]: https://console.cloud.google.com/
[cloud-sdk]: https://cloud.google.com/sdk/

## Handling dependencies

We'll use the [Swift Package Manager][spm] to manage our app's dependencies.

1.  Create a `Package.swift` file with the following contents:

    ```swift
    import PackageDescription

    let package = Package(
        name: "PerfectGAE",
        targets: [
            Target(name: "PerfectGAE", dependencies: [])
        ],
        dependencies: [
            .Package(url: "https://github.com/PerfectlySoft/Perfect-HTTPServer.git",
    majorVersion: 2, minor: 0)
        ]
    )
    ```

[spm]: https://github.com/apple/swift-package-manager

## Writing the server

1.  Create a `main.swift` with the following contents:

    ```swift
    import Foundation
    import PerfectLib
    import PerfectHTTP
    import PerfectHTTPServer

    // Create HTTP server.
    let server = HTTPServer()
    var routes = Routes()

    // Respond to App Engine health check requests
    // TODO: see #2

    // Basic GET request
    // TODO: see #3

    // Add the routes to the server.
    server.addRoutes(routes)

    // Set a listen port of 8080
    server.serverPort = 8080

    do {
        // Launch the HTTP server.
        try server.start()
    } catch PerfectError.networkError(let err, let msg) {
        print("Network error thrown: \(err) \(msg)")
    }
    ```

1.  Create a route to handle App Engine health-check requests" (per the [custom runtime docs][custom-runtime]):

    ```swift
    // Respond to App Engine health check requests
    routes.add(method: .get, uri: "/_ah/health", handler: { request, response in
        print("GET - /_ah/health route handler...")
        response.setBody(string: "OK")
        response.completed()
    })
    ```

1.  Create a route to handle `GET` requests to `/hello`:

    ```swift
    // Basic GET request
    routes.add(method: .get, uri: "/hello", handler: { request, response in
        print("GET - /hello route handler...")
        response.setBody(string: "Hello from Swift on App Engine flexible environment!")
        response.completed()
    })
    ```

[custom-runtime]: https://cloud.google.com/appengine/docs/flexible/custom-runtimes/build#lifecycle_events

## Creating the `Dockerfile`

Since Swift doesn't have an officially supported App Engine runtime, we'll
create our own.

1.  Create a `Dockerfile` with the following contents:

    ```Dockerfile
    FROM ibmcom/swift-ubuntu:latest
    LABEL Description="Docker image for Swift + Perfect on App Engine flexible environment."

    # Get extra dependencies for Perfect
    RUN apt-get update && apt-get install -y \
    openssl \
    libssl-dev \
    uuid-dev

    # Expose default port for App Engine
    EXPOSE 8080

    # Copy sources
    RUN mkdir /root/PerfectGAE
    ADD main.swift /root/PerfectGAE
    ADD Package.swift /root/PerfectGAE

    # Build the app
    RUN cd /root/PerfectGAE && swift build

    # Run the app
    USER root
    CMD ["/root/PerfectGAE/.build/debug/PerfectGAE"]
    ```

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: custom
        env: flex

1.  Run the following command to deploy your app (make take several minutes):

        gcloud app deploy

1.  Run the following command to view your app, then append `/hello` to the URL:

        gcloud app browse

If all goes well, you should see "Hello from Swift on App Engine flexible environment!".
