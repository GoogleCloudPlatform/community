# envoyfilter

This directory contains a Lua
[Istio `EnvoyFilter`](https://istio.io/docs/reference/config/networking/envoy-filter/)
that extracts a claim from a JSON Web Token (JWT) in the `Authorization` header
of an incoming request and adds the claim as an additional HTTP request header.

This additional header is used in a Istio `VirtualService` to
route requests, see [`virtualservice.yaml`](virtualservice.yaml).

## Development

See the Lua source code in [`jwtparse.lua`](jwtparse.lua).

Download third-party dependencies:

    ./get-deps.sh

Run unit tests:

    ./test.sh

## Disclaimer

This is not an officially supported Google product.
