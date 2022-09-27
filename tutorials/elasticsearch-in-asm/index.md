---
title: Create Elastic Search Cluster in ASM enabled GKE
description: Deploy a DIY Elastic Search Cluster using ECK in Anthos Service Mesh enabled GKE, with options to enforce and enable zero trust policy.
author: t-indumathy
tags: ASM, mTLS, GoogleCASIssuer, cert-manager
date_published: 2021-04-11
---

Indumathy Thiagarajan | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This Tutorial demonstrates the DIY deployment of an Elastic Search Cluster in ASM enabled GKE using [ECK operator](https://www.github.com/elastic/cloud-on-k8s). It also concentrates on applying mTLS for all the workloads with in the cluster and using Custom CA by leveraging [Certificate Authority Service](https://cloud.google.com/certificate-authority-service) for both in-mesh and edge-mesh traffic. This tutorial doesn't cover the steps for [creating a GKE Cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-regional-cluster) and [installing ASM](https://cloud.google.com/service-mesh/docs/unified-install/quickstart-asm). A basic knowledge of GKE, ASM or Istio, ElasticSearch and Kibana might be required to understand the setup explained in the tutorial.

## Objectives

*   Deploy ECK on ASM enabled GKE cluster.
*   Deploy APM Server, ElasticSearch and Kibana.
*   Configure OIDC based End-User Authentication.
*   Creating Highly Available Resilient Cluster. 

## Pre-requisites

*   GKE cluster.
*   APIs enabled.
*   ASM installed on GKE.
*   Configure kubectl.

## Deploy Elastic

Deployment of elastic-operator, apm-server, elasticsearch, kibana in ASM involves tweaking of parameters in the deployment config files.

### Install Elastic Operator

1. Download the CRD configuration file or create the CRDs directly in the cluster.

`kubectl create -f https://download.elastic.co/downloads/eck/${ECK_VERSION}/crds.yaml`

for e.g. `ECK_VERSION=2.1.0`

2. Enable `STRICT` mTLS across the mesh.

```
   apiVersion: "security.istio.io/v1beta1"
   kind: "PeerAuthentication"
   metadata:
        name: "mesh-wide"
        namespace: "istio-system"
    spec:
        mtls:
            mode: STRICT
```
3. Create  `elastic-system` Namespace for operator.

```
    apiVersion: v1
    kind: Namespace
    metadata:
        name: elastic-system
        labels:
            name: elastic-system
```
4. Label namespace with asm revision for automatic injection.

`kubectl label namespace elastic-system  istio-injection- istio.io/rev=asm-1112-17 --overwrite`

5. Install ECK operator.

`kubectl apply -f https://download.elastic.co/downloads/eck/${ECK_VERSION}/operator.yaml`

6. Validate the logs

`kubectl -n elastic-system logs statefulset.apps/elastic-operator`

### Basic ElasticSearch Setup

1. Create a namespace for deploying elastic components

```
apiVersion: v1
kind: Namespace
metadata:
    name: ${ELASTIC_NS}
    labels:
        name: ${ELASTIC_NS}
```

for e.g. `ELASTIC_NS=elastic-dev`

2. Label namespace with asm revision for automatic injection

`kubectl label namespace ${ELASTIC_NS} istio-injection- istio.io/rev=asm-1112-17 --overwrite`

3. Deploy APM Server
```
apiVersion: apm.k8s.elastic.co/v1
kind: ApmServer
metadata:
    name: elastic-asm
spec:
    version: ${ELASTIC_VERSION}
    count: 1
    elasticsearchRef:
        name: elastic-asm
    http:
        tls:
            selfSignedCertificate:
                disabled: true
    podTemplate:
        metadata:
            annotations:
                sidecar.istio.io/rewriteAppHTTPProbers: "true"
        spec:
            automountServiceAccountToken: true
```

for e.g. `ELASTIC_VERSION=8.1.2`

`selfSignedCertificate` is disabled as ASM’s MeshCA or CAS will be used to take over TLS certificates for the HTTP layer. However we cannot disable certificates in the Transport layer, and the operator by default uses a self-signed certificate for communication between nodes within the cluster. And since we will be injecting istio-proxy on all workloads and have enabled `STRICT` mTLS, there will be a double encryption happening, out of which one of them will be offloaded in the istio-proxy container.

`sidecar.istio.io/rewriteAppHTTPProbers: "true"` is required to make sure that the deployment doesn’t break because of `STRICT` mTLS with-in mesh.

`automountServiceAccountToken: true` is required to communicate with SDS and automatically rotate the certs without external intervention to restart the workloads.

`kubectl apply -f apmserver.yaml -n ${ELASTIC_NS}`

4. Deploy ElasticSearch <a name="DeployElasticSearch"></a>

```
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
    name: elastic-asm
spec:
    version: ${ELASTIC_VERSION}
    http:
        tls:
            selfSignedCertificate:
                disabled: true
    nodeSets:
        - name: default
          count: 3
          config:
            node.store.allow_mmap: true
          podTemplate:
            spec:
                automountServiceAccountToken: true
                initContainers:
                    - name: sysctl
                      securityContext:
                        privileged: true
                      command: [ 'sh', '-c', 'sysctl -w vm.max_map_count=262144' ]
                containers:
                    - name: elasticsearch
                      env:
                        - name: network.host
                          value: 0.0.0.0
```

`node.store.allow_mmap: true` makes sure that the memory map is used for storing the shard (lucene-based)indexes and `vm.max_map_count=262144` overrides the default value (65530) to avoid OOM exceptions.

`network.host: 0.0.0.0` denotes the addresses of all available network interfaces, but Elasticsearch may mostly pick up the pod IP as the publishing address. This will be used for both HTTP and Transport layer communication.

`kubectl apply -f elasticsearch.yaml -n ${ELASTIC_NS}`

5. Deploy Kibana

```
apiVersion: kibana.k8s.elastic.co/v1
kind: Kibana
metadata:
    name: elastic-asm
spec:
    version: ${ELASTIC_VERSION}
    count: 1
    elasticsearchRef:
        name: elastic-asm
    http:
        tls:
            selfSignedCertificate:
                disabled: true
    podTemplate:
        spec:
            automountServiceAccountToken: true
            containers:
                - name: kibana
                  readinessProbe:
                    httpGet:
                        scheme: HTTP
                        path: /kibana
                        port: 5601
                  env:
                    - name: SERVER_BASEPATH
                      value: "/kibana"
                    - name: SERVER_REWRITEBASEPATH
                      value: "true"
```


Modifying the environment variables: `SERVER_BASEPATH` and `SERVER_REWRITEBASEPATH` are optional. These parameters are used to change the default base path (/) of Kibana. If these parameters are overridden, it is required to modify the  `readinessProbe/httpGet` block to refer to the new base path, without which it will enter into a redirect loop.

P.S: This configuration is required only when the Kibana Virtual Service is been configured for [rewrite](#rewrite)

`kubectl apply -f kibana.yaml -n ${ELASTIC_NS}`

Once the elastic components are running successfully without any errors, their corresponding [basic ASM artifacts](#asmbasicsetup) deployment could be performed.

### OIDC ElasticSearch Setup

6. Steps 1,2 and 3 are same as the basic setup.
7. Instead of using the default self-signed certificate provided by ES, Cert-manager is leveraged to use custom CA and automatic certificate handling on the edge. 
8. Create Certificate in `${GW_NS}` and `${ELASTIC_NS}`
```
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
    name: es-cluster-certificate
spec:
    secretName: es-cluster-credential
    subject:
        organizations:
            - ${HOST_NAME}
            - elastic-asm
    dnsNames:
        - ${HOST_NAME}
        - elastic-asm-es-http
        - elastic-asm-es-http.default.svc
        - elastic-asm-es-http.default.svc.cluster.local
    duration: 24h
    renewBefore: 16h
    issuerRef:
        group: cas-issuer.jetstack.io
        kind: GoogleCASClusterIssuer
        name: cluster-cas-issuer
```
9. Deploy ElasticSearch with OIDC configuration
```
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
    name: elastic-asm
spec:
    version: ${ELASTIC_VERSION}
http:
    service:
        spec:
            type: ClusterIP
    tls:
        selfSignedCertificate:
            disabled: true
        certificate:
            secretName: es-cluster-credential
nodeSets:
    - name: default
      count: 3
      config:
        node.store.allow_mmap: true
        xpack.license.self_generated.type: trial
        xpack.security.http.ssl.enabled: true
        xpack.security.authc.token.enabled: true
        xpack.security.authc.realms.oidc.oidc1:
            order: 0
            rp.client_id: "1234567890912-a1b2c3d4e5f6g7h8in.apps.googleusercontent.com"
            rp.response_type: code
            rp.requested_scopes: ["openid", "email"]
            rp.redirect_uri: "https://<<HOST_NAME>>:9000/kibana/api/security/oidc/callback"
            op.issuer: "https://accounts.google.com"
            op.authorization_endpoint: "https://accounts.google.com/o/oauth2/v2/auth"
            op.token_endpoint: "https://oauth2.googleapis.com/token"
            op.jwkset_path: "https://www.googleapis.com/oauth2/v3/certs"
            op.userinfo_endpoint: "https://openidconnect.googleapis.com/v1/userinfo"
            rp.post_logout_redirect_uri: "https://<<HOST_NAME>>:9000/kibana/security/logged_out"
            claims.principal: email
        xpack.security.authc.realms.native.native1:
            order: 1
      podTemplate:
        metadata:
            annotations:
                traffic.sidecar.istio.io/includeInboundPorts: "*"
        spec:
            automountServiceAccountToken: true
            initContainers:
                - name: sysctl
                  securityContext:
                    privileged: true
                  command: [ 'sh', '-c', 'sysctl -w vm.max_map_count=262144 && echo "ABCDE-FgHi123KlMn789OpQr567StuV345" | bin/elasticsearch-keystore add --force --stdin xpack.security.authc.realms.oidc.oidc1.rp.client_secret' ]
            containers:
                - name: elasticsearch
                  env:
                    - name: network.host
                      value: 0.0.0.0
                    - name: READINESS_PROBE_PROTOCOL
                      value: https
```

The client_secret configured in the init container command is applicable only for testing purposes. In production or realtime setup it must be configured in the elastic key store with the setting name as `xpack.security.authc.realms.oidc.oidc1.rp.client_secret` with *client_secret* value as the `Secret` and with type as `Single string`

10. Deploy Kibana with OIDC configuration
```
apiVersion: kibana.k8s.elastic.co/v1
kind: Kibana
metadata:
    name: elastic-asm
spec:
    version: ${ELASTIC_VERSION}
    count: 1
    elasticsearchRef:
        name: elastic-asm
    http:
        tls:
            selfSignedCertificate:
                disabled: true
    podTemplate:
        spec:
            automountServiceAccountToken: true
            containers:
                - name: kibana
                  readinessProbe:
                    httpGet:
                        scheme: HTTP
                        path: /kibana
                        port: 5601
                  env:
                    - name: SERVER_BASEPATH
                      value: "/kibana"
                    - name: SERVER_REWRITEBASEPATH
                      value: "true"
    config:
        xpack.security.authc.selector.enabled: true
        xpack.security.authc.providers:
            oidc.oidc1:
                order: 0
                realm: oidc1
                description: "Login with Google"
            basic.basic1:
                order: 1
```

After the elastic OIDC setup is complete,  their corresponding [TLS ASM artifacts](#asmtls) deployment could be performed.
### HA ElasticSearch Setup
1. Create Static Provisioning of the Storage Class (if required with [CMEK](https://cloud.google.com/kubernetes-engine/docs/how-to/using-cmek#storage-key)) with `reclaimPolicy: Retain`
2. Use this Storage Class in the ES deployment config
```
spec:
    version: ${ELASTIC_VERSION}
    volumeClaimDeletePolicy: DeleteOnScaledownOnly
    ...
    ...
    ...
        volumeClaimTemplates:
            - metadata:
                name: elasticsearch-data
              spec:
                accessModes:
                    - ReadWriteOnce
                resources:
                    requests:
                        storage: 500Gi
                storageClassName: elastic-static-sc
```
3. Zone awareness attributes can be used to avoid SPOF, and will enable ES to distribute the shards to different zones in the event of a failure. Kubernetes node attributes are used for configuring the allocation awareness attributes.
4. A typical ES-HA/DR configuration can include configurations for:

    a. Auto-scaling - `elasticsearch.alpha.elastic.co/autoscaling-spec` <br>
    b. Preserving volumes - `volumeClaimDeletePolicy: DeleteOnScaledownOnly` <br>
    c. Allocation Awareness -
    - `eck.k8s.elastic.co/downward-node-labels: "topology.kubernetes.io/zone"` <br>
    - `node.attr.zone: ${ZONE}` <br>
    - `cluster.routing.allocation.awareness.attributes: zone` <br>
<pre>
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: elastic-asm
  annotations:
    <b>eck.k8s.elastic.co/downward-node-labels</b>: "topology.kubernetes.io/zone"
    <b>elasticsearch.alpha.elastic.co/autoscaling-spec</b>: |
      {
          "policies": [{
              "name": "data-as",
              "roles": ["data"],
              "deciders": {
                "proactive_storage": {
                    "forecast_window": "5m"
                }
              },
              "resources": {
                  "nodeCount": { "min": 3, "max": 5 },
                  "cpu": { "min": 2, "max": 5 },
                  "memory": { "min": "1Gi", "max": "32Gi" },
                  "storage": { "min": "8Gi", "max": "256Gi" }
              }
          }]
      }
spec:
  version: ${ELASTIC_VERSION}
  <b>volumeClaimDeletePolicy</b>: DeleteOnScaledownOnly
  http:
    service:
      spec:
        type: ClusterIP
    tls:
      selfSignedCertificate:
        disabled: true
      certificate:
        secretName: es-cluster-credential
  nodeSets:
    - name: master-nodes
      count: 3
      config:
        <b>node.attr.zone</b>: ${ZONE}
        <b>cluster.routing.allocation.awareness.attributes</b>: zone
        node.store.allow_mmap: true
        node.roles: ["master"]
        node.remote_cluster_client: false
        xpack.license.self_generated.type: trial
        xpack.security.http.ssl.enabled: true
        xpack.security.authc.token.enabled: true
        xpack.security.authc.realms.oidc.oidc1:
          order: 0
          rp.client_id: "1234567890912-a1b2c3d4e5f6g7h8in.apps.googleusercontent.com"
          rp.response_type: code
          rp.requested_scopes: ["openid", "email"]
          rp.redirect_uri: "https://<<HOST_NAME>>:9000/kibana/api/security/oidc/callback"
          op.issuer: "https://accounts.google.com"
          op.authorization_endpoint: "https://accounts.google.com/o/oauth2/v2/auth"
          op.token_endpoint: "https://oauth2.googleapis.com/token"
          op.jwkset_path: "https://www.googleapis.com/oauth2/v3/certs"
          op.userinfo_endpoint: "https://openidconnect.googleapis.com/v1/userinfo"
          rp.post_logout_redirect_uri: "https://<<HOST_NAME>>:9000/kibana/security/logged_out"
          claims.principal: email
        xpack.security.authc.realms.native.native1:
          order: 1
      podTemplate:
        metadata:
          annotations:
            traffic.sidecar.istio.io/includeInboundPorts: "*"
        spec:
          automountServiceAccountToken: true
          initContainers:
            - name: sysctl
              securityContext:
                privileged: true
              command: [ 'sh', '-c', 'sysctl -w vm.max_map_count=262144 && echo "ABCDE-FgHi123KlMn789OpQr567StuV345" | bin/elasticsearch-keystore add --force --stdin xpack.security.authc.realms.oidc.oidc1.rp.client_secret' ]
          containers:
            - name: elasticsearch
              env:
                - name: network.host
                  value: 0.0.0.0
                - name: READINESS_PROBE_PROTOCOL
                  value: https
                - name: ZONE
                  valueFrom:
                    fieldRef:
                      fieldPath: <b>metadata.annotations['topology.kubernetes.io/zone']</b>
            <b>topologySpreadConstraints</b>:
              - maxSkew: 1
                topologyKey: topology.kubernetes.io/zone
                whenUnsatisfiable: DoNotSchedule
                  labelSelector:
                    matchLabels:
                      elasticsearch.k8s.elastic.co/cluster-name: elastic-asm
                      elasticsearch.k8s.elastic.co/statefulset-name: elastic-asm-es-default
    - name: ingest-data-nodes
      count: 3
      config:
        node.store.allow_mmap: true
        node.roles: ["data", "ingest"]
...
...
...
</pre>
## Create ASM Artifacts
Creation of ASM networking artifacts - Gateways, Virtual Services to access Elastic and Kibana services.
<a id="asmbasicsetup"></a>
### Basic Setup
####Customize Istio IngressGateway
Assuming that the Istio Ingress Gateway is already installed in a separate namespace - gateway, additional ports can be added in the Service config to access both elasticsearch and kibana endpoints.
```
apiVersion: v1
kind: Service
metadata:
  name: istio-ingressgateway
  labels:
    app: istio-ingressgateway
    istio: ingressgateway
spec:
  ports:
    # status-port exposes a /healthz/ready endpoint that can be used with GKE Ingress health checks
    - name: status-port
      port: 15021
      protocol: TCP
      targetPort: 15021
    # Any ports exposed in Gateway resources should be exposed here.
    - name: http2
      nodePort: 32412
      port: 80
      protocol: TCP
      targetPort: 8080
    - name: https
      nodePort: 32500
      port: 443
      protocol: TCP
      targetPort: 8443
    - name: kibana
      nodePort: 32726
      port: 9000
      protocol: TCP
      targetPort: 9000
    - name: es
      nodePort: 32248
      port: 9090
      protocol: TCP
      targetPort: 9090
  selector:
    istio: ingressgateway
    app: istio-ingressgateway
  type: LoadBalancer
```

`kubectl apply -f istio-ingress-gw.yaml -n ${GW_NS}`


for e.g. `GW_NS=gateway`
####Elastic Gateway and VirtualService
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: es-gateway
  namespace: ${GW_NS}
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 9090
        name: https-elastic
        protocol: HTTPS
      hosts:
        - "*"
      tls:
        credentialName: elastic-credential
        mode: SIMPLE
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: es-gw-vs
spec:
  hosts:
    - "*"
  gateways:
    - ${GW_NS}/es-gateway
  http:
    - route:
      - destination:
          host: elastic-asm-es-http
          port:
            number: 9200
```
	
Port: `9200` is used for all HTTP based communications with elastic.

`kubectl apply -f es-gw.yaml`


Hitting the url `https://<<HOST_NAME>>:9090/` will access the elastic endpoint.
####Kibana Gateway and VirtualService
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: kibana-gateway
  namespace: ${GW_NS}
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 9000
        name: https-kibana
        protocol: HTTPS
      hosts:
        - "*"
      tls:
        credentialName: elastic-credential
        mode: SIMPLE
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: kibana-gw-vs
spec:
  hosts:
    - "*"
  gateways:
    - ${GW_NS}/kibana-gateway
  http:
    - name: kibana-route
      route:
        - destination:
            host: elastic-asm-kb-http
            port:
              number: 5601
```
	
Port: `5601` is used for all HTTP based communications with Kibana. 

<a id="rewrite"></a>
#### (Optional) VirtualService Setup

If a different url is required for accessing the kibana UI, a rewrite option is used.
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: kibana-gw-vs
spec:
  hosts:
    - "*"
  gateways:
    - ${GW_NS}/kibana-gateway
  http:
    - match:
        - uri:
            prefix: "/kibana/"
      rewrite:
        uri: "/"
      route:
        - destination:
            host: elastic-asm-kb-http
            port:
              number: 5601
```

`kubectl apply -f kibana-gw.yaml`


Hitting the url `https://<<HOST_NAME>>:9000/kibana` will access the kibana endpoint.
<a id="asmtls"></a>
###TLS Setup

####Elastic Gateway and VirtualService
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: es-gateway
  namespace: gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 9090
        name: https-elastic
        protocol: HTTPS
      hosts:
        - "*"
      tls:
        mode: PASSTHROUGH
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: es-gw-vs
spec:
  hosts:
    - "*"
  gateways:
    - gateway/es-gateway
  tls:
    - match:
        - sniHosts: [ "${HOST_NAME}" ]
      route:
        - destination:
            host: elastic-asm-es-http
            port:
              number: 9200
```
####Kibana Gateway and VirtualService
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: kibana-gateway
  namespace: gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 9000
        name: https-kibana
        protocol: HTTPS
      hosts:
        - "*"
      tls:
        credentialName: es-cluster-credential
        mode: SIMPLE
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: kibana-gw-vs
spec:
  hosts:
    - "*"
  gateways:
    - gateway/kibana-gateway
  http:
    - name: kibana-route
      route:
        - destination:
            host: elastic-asm-kb-http
            port:
              number: 5601
```

## What's next

- Learn more about [Istio HTTPRewrite](https://istio.io/latest/docs/reference/config/networking/virtual-service/#HTTPRewrite).
- Learn more about [Certificate Management in ASM](https://cloud.google.com/service-mesh/docs/automate-tls#deploy_a_sample_application).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
