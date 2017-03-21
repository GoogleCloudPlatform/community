---
title: Vapor on Google App Engine Tutorial
description: Learn how to build an app with Swift and Vapor in the Google App Engine environment.
author: mpmcdonald
tags: App Engine, Swift, Vapor
date_published: 2017-03-21
---
This tutorial shows a sample [Swift][swift] app built with [Vapor][vapor]
deployed to the Google App Engine flexible environment.

Vapor is "a web framework and server for Swift that works on macOS and Ubuntu."
It is [open source on GitHub][vapor-github].

This tutorial assumes basic familiarity with Swift programming.

[swift]: http://swift.org
[vapor]: https://vapor.codes
[vapor-github]: https://github.com/vapor/vapor

## Objectives

1. Create a Swift "Hello, world" app that uses the Vapor framework.
1. Deploy the app to Google App Engine flexible environment.

## Costs

This tutorial uses billable components of Google Cloud Platform, including:

- Google App Engine flexible environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK][cloud-sdk].

[console]: https://console.cloud.google.com/
[cloud-sdk]: https://cloud.google.com/sdk/

## Handling dependencies

We'll use the [Swift Package Manager][spm] to manage our app's dependencies.

1.  Create a `package.swift` file with the following contents:

```swift
import PackageDescription

let package = Package(
    name: "VaporGAE",
    targets: [
        Target(name: "VaporGAE", dependencies: [])
    ],
    dependencies: [
        .Package(url: "https://github.com/vapor/vapor.git", majorVersion: 1, minor: 1)
    ]
)
```

[spm]: https://github.com/apple/swift-package-manager

## Writing the server

1.  Create a `main.swift` with the following contents:

```swift
import Foundation
import Vapor

let drop = Droplet()

// Respond to GAE health check requests
...

// Basic GET request
...

// Start server on 8080 (default)
drop.run()
```

1.  Create a route to handle GAE "health check" requests" (per the [custom runtime docs][custom-runtime]):

```swift
// Respond to GAE health check requests
drop.get("/_ah/health") { request in
    print("ALL - /_ah/health route handler...")
    return "OK"
}
```

1.  Create a route to handle `GET` requests to `/hello`:

```swift
// Basic GET request
drop.get("/hello") { request in
    print("GET - /hello route handler...")
    return "Hello from Vapor on GAE!"
}
```

[custom-runtime]: https://cloud.google.com/appengine/docs/flexible/custom-runtimes/build#lifecycle_events

## Creating the `Dockerfile`

Since Swift doesn't have an officially supported GAE runtime, we'll create our
own.

1.  Create a `Dockerfile` with the following contents:

```
FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Kitura on GAE."

# Expose default port for GAE
EXPOSE 8080

# Add app source
ADD . /app
WORKDIR /app

# Build release
RUN swift build --configuration release

# Run the app
ENTRYPOINT [".build/release/VaporGAE"]
```

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

```
runtime: custom
env: flex
```

1.  Run the following command to deploy your app (make take several minutes):

```
gcloud app deploy
```

1.  Run the following command to see your deployed app:

```
gcloud app browse
```

Add `/hello` to the end of the URL, and if all goes well, you should see
"Hello from Vapor on GAE!" in your browser.
