---
title: Node.js and Google Cloud Platform
description: Get an overview of Node.js and learn ways to run Node.js apps on Google Cloud Platform.
author: jmdobry
tags: Node.js, Compute Engine, Kubernetes Engine, App Engine, Cloud Functions
date_published: 2016-12-14
---
This tutorial shows how to prepare your computer for [Node.js][nodejs]
development. Follow this tutorial to install Node.js and relevant tools.

## Objectives

* Get an overview of Node.js
* Learn ways to run Node.js app on Google Cloud Platform

## What is Node.js?

**tldr;** [Node.js][nodejs] is an evented I/O framework built on the
[V8 JavaScript engine][v8]. It is intended for writing scalable network programs
such as web servers.

### Event-driven programming

Event-driven programming is the idea that events control of the flow of a
program. When an event occurs, code registered to handle the event is executed.
When performing I/O, traditional programming is commonly synchronous, meaning
that an executing thread must wait for the I/O operation to complete before it
can continue its execution. Solutions such as multi-threading were devised in
order to improve CPU utilization by switching between threads when a thread
blocks. Multi-threading does however introduce the overhead of switching between
threads and remembering each thread’s context.

At the heart of Node.js is an event loop that performs two tasks: Check to see
if an event has occurred and if so, execute the registered event handler. This
allows Node.js to maintain a single thread that is constantly working, executing
event handlers as events occur.

### Node.js is JavaScript

JavaScript is the language of Node.js. JavaScript has the concept of a closure:
a function which remembers the context in which is was declared, allowing it to
access that same context when it is executed later. This is perfect for
event-driven programming. The programmer can register functions as event
handlers, and when the event finally occurs these functions are then executed in
the context in which the programmer intended. Along with this come the other
features (and idiosyncrasies) of JavaScript: basic data types, prototypal
inheritance, loops, conditionals, etc. Node.js also comes with a set of core
libraries that make up the I/O framework and provide other useful functionality.

### Buffers

Node.js was originally written to handle text—specifically HTML. The
[`Buffer`][buffer] class was introduced to allow Node.js to handle binary data.
Buffers are chunks of memory allocated outside of the JavaScript VM and are
therefore immune to some of the normal effects of garbage collection. Buffers
can be sliced and copied. The individual bytes of a Buffer can be manipulated.
Buffers can be created from Strings of various encodings, and can be converted
into Strings of various encodings. Buffers give Node.js a range of capabilities
that increase the usefulness of Node.js.

### Node.js Module System

Node.js does away with the global namespace and implements the CommonJS
standard (though ES2015 modules are on the way). Files and modules have a
one-to-one relationship. Each file chooses exactly what will be publicly exposed
by the file’s module when it is loaded by other modules. Node.js looks for core
modules first, then modules with relative path names, and finally looks in
`node_modules` when searching for modules. Each module is cached the first
time it is loaded, so the contents of each module are only initialized once.

### Node.js Core Library and Ecosystem

The Node.js core library provides the developer with a number of tools for
performing I/O, working with HTTP, files, the OS, streams, and much more. In
addition, [npm][npm] is a large repository of community and open source packages
for Node.js. Node.js is at home in small, rapidly developing products, probably
because Node.js and its ecosystem are still (relatively) small and under rapid
development. Node.js is emerging in the enterprise as the ecosystem grows, as
the runtime matures, and as it gains improved robustness and
[debugging capabilities][inspect].

## Running Node.js Apps on Google Cloud Platform

There are five options for running Node.js applications on Google Cloud
Platform:

* [Google Compute Engine][gce]
* [Google Kubernetes Engine][gke]
* [Google App Engine flexible environment][gae-flex]
* [Google App Engine standard environment][gae-standard]
* [Google Cloud Functions][gcf]

### Node.js on Compute Engine

Hosting a Node.js application on [Compute Engine][gce] is just like hosting a
Node.js application on a traditional Virtual Private Server (VPS)—you have
complete control of the virtual machine. Google Compute Engine delivers virtual
machines running in Google's innovative data centers and worldwide fiber
network. Compute Engine's tooling and workflow support enable scaling from
single instances to global, load-balanced cloud computing.

### Node.js on Kubernetes Engine

[Kubernetes Engine][gke] is a powerful cluster manager and orchestration system
for running your Docker containers. Kubernetes Engine schedules your containers
into the cluster and manages them automatically based on requirements you define
(such as CPU and memory). It's built on the open source [Kubernetes][k8s]
system, giving you the flexibility to take advantage of on-premises, hybrid, or
public cloud infrastructure. With it you can orchestrate containerized Node.js
deployments using Kubernetes' container management infrastructure.

### Node.js on App Engine flexible environment

[App Engine flexible environment][gae-flex] is a fully managed, Docker-based
Platform-as-a-Service (PaaS). You can deploy, monitor, and scale Node.js
applications without having to know anything about virtual machines, containers,
or compute infrastructure. Google manages your Node.js application for you.

### Node.js on App Engine standard environment

The Node.js runtime in the [App Engine stanard environment][gae-standard] runs
within containers inside of secure sandboxes and can balance load by automatically
scaling. At any given time, your application can be running on one or many
instances with requests being spread across all of them. Each instance includes a
security layer to ensure that instances cannot inadvertently affect each other.

### Node.js on Cloud Functions

[Cloud Functions][gcf] is a lightweight, event-based, asynchronous compute
solution that allows you to create small, single-purpose functions that respond
to cloud events without the need to manage a server or a runtime environment.
You deploy individual functions written in Node.js that are executed in response
to various cloud events, including direct HTTP requests.

Learn [how to prepare a Node.js development environment][nodejs-dev] and read
more about [Node.js on Google Cloud Platform][nodejs-gcp].

[nodejs]: https://nodejs.org/
[v8]: https://developers.google.com/v8/
[buffer]: https://nodejs.org/api/buffer.html
[nodejs-dev]: how-to-prepare-a-nodejs-dev-environment
[inspect]: https://nodejs.org/api/debugger.html#debugger_v8_inspector_integration_for_node_js
[npm]: https://www.npmjs.com/
[gce]: https://cloud.google.com/compute/
[gke]: https://cloud.google.com/kubernetes-engine/
[k8s]: http://kubernetes.io/
[gae-flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
[gae-standard]: https://cloud.google.com/appengine/docs/standard/nodejs/
[gcf]: https://cloud.google.com/functions/
[nodejs-gcp]: https://cloud.google.com/nodejs/
