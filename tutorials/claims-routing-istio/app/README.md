# Sample app for tutorial on Istio routing based on JWT claims

Sample code showing how Istio can route end-user traffic based on
custom claims in JSON Web Tokens (JWTs), using
[Identity Platform](https://cloud.google.com/identity-platform/) ID tokens.

Read the tutorial in [`../index.md`](../index.md).

## Development

Set the `BETA` environment variable to `true` to enable the beta endpoints (`beta` and `api/beta`).

Set the `DEBUG` environment variable to `true` to enable additional debug logging, such as logging
request headers of API requests.

## Disclaimer

This is not an officially supported Google product.
