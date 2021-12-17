---
title: Building Python Serverless REST Applications
description: Goblet is a framework for writing serverless rest apis in python in google cloud. It allows you to quickly create and deploy python apis backed by api gateway and cloudfunctions.
author: anovis
tags: cloudfunction, api gateway, goblet
date_published: 2021-12-18
---

Austen Novis | Software developer | premise.com

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>


### Getting Started

In this tutorial, you'll use the goblet command line utility to create and deploy a basic REST API, which behind the scenes will create an api gateway and a cloudfunction. This quickstart uses Python 3.9. You can find the latest versions of python on the Python download page. Make sure to have `api-gateway` and `cloudfunctions` enabled in your gcp project.


To install Goblet, we'll first create and activate a virtual environment in python3.9:

```sh
$ python3 --version
Python 3.9.9
$ python3 -m venv venv37
$ . venv37/bin/activate
```

Next we'll install Goblet using pip:

```sh
python3 -m pip install goblet-gcp
```

You can verify you have goblet installed by running:

```sh
$ goblet --help
Usage: goblet [OPTIONS] COMMAND [ARGS]...
...
```

### Credentials

Before you can deploy an application, be sure you have credentials configured. You should run `gcloud auth application-default login` and sign in to the desired project.

When setting the defaut location note that api-gateway is only available in `asia-east1`, `europe-west1`, `us-east-1` and `us-central1`.

### Creating Your Api Files

You can create your project files by creating a new directory and running `goblet init API_NAME` or manually create the files main.py and requirements.txt. Make sure requirements.txt includes `goblet-gcp`

```sh
$ ls -la
drwxr-xr-x   .goblet
-rw-r--r--   main.py
-rw-r--r--   requirements.txt
```

You can ignore the .goblet directory for now, which  the two main files we'll focus on is `app.py` and` requirements.txt`.

Let's take a look at the main.py file:

```python
from goblet import Goblet, goblet_entrypoint

app = Goblet(function_name="goblet_example")
goblet_entrypoint(app)

@app.route('/hello')
def home():
    return {"hello": "world"}

@app.route('/bye')
def home():
    return {"bye": "world"}
```

This app will deploy an api with endpoints `/hello` and `/bye`.

### Running Locally

Running your functions locally for testing and debugging can be done by running the command `goblet local`.

Now you can hit your functions endpoints at `localhost:8080/hello` and `localhost:8080/bye`

### Deploying

Let's deploy this app. Make sure you're in the app directory and run goblet deploy making sure to specify the desired location:

```sh
$ goblet deploy -l us-central1 -p PROJECT
INFO:goblet.deployer:zipping function......
INFO:goblet.deployer:uploading function zip to gs......
INFO:goblet.deployer:function code uploaded
INFO:goblet.deployer:creating cloudfunction......
INFO:goblet.deployer:deploying api......
INFO:goblet.deployer:api successfully deployed...
INFO:goblet.deployer:api endpoint is goblet-example-yol8sbt.uc.gateway.dev
```

You now have an API up and running using API Gateway and cloudfunctions:

```sh
$ curl https://goblet-example-yol8sbt.uc.gateway.dev/hello

{"hello": "world"}
```

You've now created your first app using goblet. You can make modifications to your main.py file and rerun goblet deploy to redeploy your changes.

### Destroying Resources

If you're done experimenting with Goblet and you'd like to cleanup, you can use the `goblet destroy -l us-central1 -p PROJECT` command making sure to specify the desired location, and Goblet will delete all the resources it created when running the goblet deploy command.

```sh
$ goblet destroy -l us-central1 -p PROJECT
INFO:goblet.deployer:destroying api gateway......
INFO:goblet.deployer:api configs destroying....
INFO:goblet.deployer:apis successfully destroyed......
INFO:goblet.deployer:deleting google cloudfunction......
```

### Next Steps

At this point, there are several next steps you can take.

Docs - [Goblet Documentation](https://anovis.github.io/goblet/docs/build/html/index.html)

Code - [Github](https://github.com/anovis/goblet)

### Blog Posts

[Tutorial: Publishing GitHub Findings to Security Command Center](https://engineering.premise.com/tutorial-publishing-github-findings-to-security-command-center-2d1749f530bc)

[Tutorial: Cost Spike Alerting](https://engineering.premise.com/tutorial-cost-spike-alerting-for-google-cloud-platform-gcp-46fd26ae3f6a)

### Examples

[Goblet Examples](https://github.com/anovis/goblet/blob/master/examples/main.py)
