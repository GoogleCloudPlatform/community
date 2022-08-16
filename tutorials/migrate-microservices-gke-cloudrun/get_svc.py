#!/usr/bin/env python3
import urllib.request
import yaml
from string import Template
import os

output_dir = 'output'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

connector_val = os.getenv('VPC_CONNECTOR', 'example-connector')
lb_dns_port = 'microservice.example.com'
template_str = '''
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  annotations:
    run.googleapis.com/ingress: $ingress
    run.googleapis.com/ingress-status: $ingress
  name: $name
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/vpc-access-connector: $connector
        run.googleapis.com/vpc-access-egress: all-traffic
    spec:
      containers:
      - name: server
        image: $image
        ports:
        - containerPort:  $container_port
          $h2c
        env: $env_vars
'''
template_obj = Template(template_str)

url = 'https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml'

req = urllib.request.Request(url)


def get_add_val(v):
    if 'REDIS_ADDR' in v['name']:
        v['value'] = 'redis.example.com:6379'
    elif 'ADDR' in v['name']:
        v['value'] = 'microservice.example.com:80'
    return v


with urllib.request.urlopen(req) as resp:
    file_str = resp.read()
    docs = yaml.safe_load_all(file_str)

    for doc in docs:
        name_val = doc['metadata']['name']
        if (doc.get('kind') == 'Deployment'
            and name_val != 'loadgenerator'
                and name_val != 'redis-cart'):
            if name_val == 'frontend':
                ingress_val = 'all'
                h2c_val = ''
            else:
                ingress_val = 'internal'
                h2c_val = 'name: h2c'

            container = doc['spec']['template']['spec']['containers'][0]
            image_val = container['image']
            container_port_val = container['ports'][0]['containerPort']
            env_vars_val = [get_add_val(v)
                            for v in container['env'] if v['name'] != 'PORT']

            final_yaml = template_obj.substitute(name=name_val, connector=connector_val,
                                                 ingress=ingress_val, h2c=h2c_val,
                                                 image=image_val, container_port=container_port_val,
                                                 env_vars=env_vars_val)

            with open(f"{output_dir}/{name_val}.yaml", "w") as f:
                f.write(final_yaml)
