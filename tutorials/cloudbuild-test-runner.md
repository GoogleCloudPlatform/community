---
title: Using Google Cloud Build as a Test Runner
description: Learn how to use Google Cloud Build as a test runner.
author: tmatsuo
tags: Google Cloud Build, Testing, PHP
date_published: 2017-02-01
---
## Google Cloud Build

[Google Cloud Build][builder] lets you create [Docker][docker]
container images from your source code. [Google Cloud SDK][cloudsdk] provides
`container builds` subcommand for utilizing this service easily.

[builder]: https://cloud.google.com/cloud-build
[docker]: https://www.docker.com/
[cloudsdk]: https://cloud.google.com/sdk/

For example, here is a simple command to build a docker image:

    gcloud builds submit -t gcr.io/my-project/my-image .

This command will send the files in the current directory to Google Cloud
Storage, then on one of the Cloud Build VMs, fetch the source code, run
`Docker build` and upload the image to [Google Container Registry][registry].

[registry]: https://cloud.google.com/container-registry/

By default, Cloud Build runs `docker build` command for building the
image. You can also customize the build pipeline by having custom build steps
described below.

## Cloud Build build steps

Cloud Build's build pipeline consists of one or more "Build Steps".
A "Build Step" is normally defined by the name of a Docker image and a list of
arguments. For more details, see the [official document][config] about the
configuration file.

[config]: https://cloud.google.com/cloud-build/docs/config

## Running tests in a build step

If we can use any arbitrary Docker image as the Build Step, and the source code
is available, then we can run unit tests as a Build Step. By doing so, you always
run the test with the same docker image. You don't have to worry about environment
differences on CI systems any more.

There is a demo repository at [cloudbuild-test-runner-example][repo]. This
tutorial uses the demo repository as part of its instructions.

[repo]: https://github.com/GoogleCloudPlatform/cloudbuild-test-runner-example

## Test runner for phpunit

The test runner is in the [`php/test/runner`][testrunner] subdirectory with the
following two files.

[testrunner]: https://github.com/GoogleCloudPlatform/cloudbuild-test-runner-example/tree/master/php/test/runner

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

The second file is `run_tests.sh`:

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

`Dockerfile` installs php5, composer, and phpunit, then has the `run_test.sh`
as the `ENTRYPOINT`.

`run_tests.sh` basically runs `composer install` and `phpunit`.

We have already built and pushed this image to
`gcr.io/cloud-dpes/phpunit-test-runner` with the following command:

```
gcloud builds submit -t gcr.io/cloud-dpes/phpunit-test-runner .
```

## Configuration file for Cloud Build

To run the tests, we need to have a configuration file to utilize our test
runner. Here is an example `cloudbuild.yaml` file.

```yaml
steps:
- name: gcr.io/cloud-dpes/phpunit-test-runner
```

## Travis Configuration file

Here is an excerpt from `.travis.yml`:

```yaml
install:
- php scripts/dump_credentials.php
- scripts/install_gcloud.sh

script:
- pushd php
- gcloud container builds submit --config=cloudbuild.yaml .
- popd
```

To use `gcloud builds` command, we need to install Google Cloud
SDK and configure it to use a service account. For more details about
prerequisites, see [the TRAVIS.md file in the repo][travis].

[travis]: https://github.com/GoogleCloudPlatform/cloudbuild-test-runner-example/blob/master/TRAVIS.md

The `gcloud builds submit` command in the `script` section
actually runs our test. If test fails on the Container Builder VM, the whole
test build will fail too.

## Next Steps

* Learn more about the [Cloud Build](https://cloud.google.com/cloud-build/docs/)
* Learn more about the [Container Registry](https://cloud.google.com/container-registry/docs/)
* Customize this tutorial to your project. For example, you may want to add
  another step for reporting test coverage, or you want to use junit, instead of
  phpunit.
* If you successfuly run your tests with Google Cloud Build and you
  think your how-to will benefit others, consider submitting another tutorial at
  [our community site](https://cloud.google.com/community/write).
