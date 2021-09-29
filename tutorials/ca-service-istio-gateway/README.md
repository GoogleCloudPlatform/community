# ca-service-istio-ingress-gateway

Tutorial showing how to configure the Istio ingress gateway to use TLS
certificates managed by `cert-manager`, using
[Certificate Authority Service](https://cloud.google.com/certificate-authority-service/docs)
as a private certificate authority (CA).

## Tutorial

Read the tutorial in [`index.md`](index.md).

## Changes

If any of the shell scripts or Kubernetes manifests associated with the
tutorial change, update the contents of `index.md` as follows:

1.  Install the
    [`embedmd` fork that supports indented commands](https://github.com/halvards/embedmd):

    ```sh
    go install github.com/halvards/embedmd@main
    ```

2.  Update the contents of `index.md` with the latest changes:

    ```sh
    embedmd -w index.md
    ```

## Disclaimer

This is not an officially supported Google product.
