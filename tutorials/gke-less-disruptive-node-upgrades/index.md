# Overview

This is a hands on tutorial and demo that demonstrates how GKE helps with reducing disruption of the workloads during node upgrades with the help of Surge Upgrade feature. We will build a demo application that uses some kind of a limited resource (like a connection pool to backend system, which we will emulate only). Then we deploy this application to a GKE cluster and start a client that puts load on the system. Then we’ll upgrade the node pool with and without surge upgrade and measure the error rate on the client side.
