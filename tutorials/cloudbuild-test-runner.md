---
title: Using Google Cloud Container Builder as a test runner
description: Learn how to use Google Cloud Container Builder as a test runner.
author: tmatsuo
tags: Google Cloud Container Builder, Testing, PHP
date_published: 02/01/2017
---
## Google Cloud Container Builder

[Google Cloud Container Builder](https://cloud.google.com/container-builder) lets
you create [Docker](https://www.docker.com/) container images from
your source code. Google Cloud SDK provides `container builds` sub
command for utilizing this service easily.

For example, here is the simple command to build a docker image.

    gcloud beta container builds submit -t gcr.io/my-project/my-image .

Under the cover, this command will send the files in the current
directory to Google Cloud Storage, then on one of the Container
Builder VMs, fetch the source code, run `Docker build` and upload the
image to [Google Container Registry](https://cloud.google.com/container-registry/).

By default, Google Cloud Container Builder runs `docker build` command
for building the image. You can also customize the build pipeline by
having custom Build Steps described below.

## Container Builder Build Steps

Google Cloud Container Builder's build pipeline consists of one or
more `Build Steps`. A `Build Step` is normally defined by the name of
a Docker image and a list of arguments. For more details, see
the [official document](https://cloud.google.com/container-builder/docs/config)
about the configuration file.

## Running test in a Build Step

If we can use arbitrary Docker image as the Build Step, and the source
code is available, there is nothing prevents us from running tests!
Since you always run the test with the same docker image, you don't
have to worry about environment differences on CI systems any more.

We have a demo repository
at [cloudbuild-test-runner-example](https://github.com/GoogleCloudPlatform/cloudbuild-test-runner-example).
We will walk through the demo repository in this tutorial.

## Test runner for phpunit

The test runner is in `php/test/runner` subdirectory of the repo with
following two files.

The first file is `Dockerfile`:

```Dockerfile
FROM alpine

RUN mkdir -p /opt/bin
ENV PATH=${PATH}:/opt/bin:/opt/gcloud/google-cloud-sdk/bin

# Install PHP and tools
RUN apk add php5 php5-openssl php5-json php5-phar php5-dom php5-bcmath wget \
    ca-certificates coreutils unzip --update && \
    php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');" && \
    php -r "if (hash_file('SHA384', 'composer-setup.php') === rtrim(file_get_contents('https://composer.github.io/installer.sig'))) { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;" && \
    php composer-setup.php --filename=composer --install-dir=/opt/bin && \
    php -r "unlink('composer-setup.php');" && \
    wget -nv https://phar.phpunit.de/phpunit.phar && \
    chmod +x phpunit.phar && \
    mv phpunit.phar /opt/bin/phpunit && \
    apk del wget unzip && \
    rm -rf /var/cache/apk/*

COPY run_tests.sh /run_tests.sh
ENTRYPOINT ["/run_tests.sh"]
```

and `run_tests.sh`:

```bash
#!/bin/bash
set -ex

if [ "$#" -eq 0 ]; then
  TEST_DIR='/workspace'
else
  TEST_DIR=${1}
fi
cd ${TEST_DIR}

if [ -f composer.json ]; then
    composer install
fi

phpunit
```

`Dockerfile` installs php5, composer, and phpunit, then has the
`run_test.sh` as the `ENTRYPOINT`.

`run_tests.sh` basically runs `composer install` and `phpunit`.

We have already built and pushed this image to
`gcr.io/cloud-dpes/phpunit-test-runner` by the following command:

```
gcloud beta container builds submit -t gcr.io/cloud-dpes/phpunit-test-runner .
```

## Configuration file for Cloud Container Builder

To run the tests, we need to have a configuration file to utilize our
test runner. Here is an example `cloudbuild.yaml` file.

```yaml
steps:
        - name: gcr.io/cloud-dpes/phpunit-test-runner
```

## Travis Configuration file

Here is an excerpt from `.travis.yml`:

```
install:
- php scripts/dump_credentials.php
- scripts/install_gcloud.sh

script:
- pushd php
- gcloud beta container builds submit --config=cloudbuild.yaml .
- popd
```

To use `gcloud beta container builds` command, we need to install
gcloud sdk and configure it to use a service account. For more details about prerequisites, see
[the TRAVIS.md file in the repo](https://github.com/GoogleCloudPlatform/cloudbuild-test-runner-example/blob/master/TRAVIS.md).

The `gcloud beta container builds submit` command in the `script`
section actually runs our test. If test fails on the Container Builder
VM, the whole test build will fail too.

## Next Steps

1. Learn more about [Google Cloud Container Builder](https://cloud.google.com/container-builder/docs/)
1. Learn more about [Container Registry](https://cloud.google.com/container-registry/docs/)
1. Customize this tutorial to adapt your project. For example, you may want to add another step for reporting test coverage, or you want to use junit, instead of phpunit.
1. If you successfuly run your tests with Google Cloud Container Builder and you think your how-to will benefit others, consider submitting another tutorial at [our community site](https://cloud.google.com/community/write).
