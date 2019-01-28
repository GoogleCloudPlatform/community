---
title: Get Started with Bitnami Django on Google Cloud Platform
description: Create and deploy a basic Django Web application on Google Cloud Platform with Bitnami Django.
author: vikram-bitnami
tags: django, python, Google Cloud Platform, bitnami
date_published: 2017-03-15
---

This tutorial demonstrates how to create and deploy a basic "hello world" Django Web application on Google Cloud Platform in just a few minutes using Bitnami Django.

## Objectives

* Install Bitnami Django on a Google Compute Engine instance.
* Create a "hello world" Django application.
* Serve the application with Apache.
* Configure a database (optional).

## Before you begin

Before starting this tutorial, ensure that you have set up a Google Cloud Platform project. You can use an existing project or [create a new project](https://console.cloud.google.com/project).

## Cost

The default configuration allows you to run a low-traffic Web application powered by Django using an `f1-micro` instance with a standard 10 GB persistent disk. You can customize the configuration when deploying this solution or change it later, although the default configuration is fine for the purposes of this tutorial.

Estimated cost for the above default configuration is $4.28 per month, based on 30-day, 24 hours per day usage in the Central US region. Sustained use discount is included.

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage. New Google Cloud customers may be eligible for a [free trial](https://cloud.google.com/free-trial).

## Deploy Bitnami Django on a Google Compute Engine instance

Deploy Bitnami Django on a Google Compute Engine instance:

1. From the Google Cloud Platform menu, select the [Cloud Launcher](https://console.cloud.google.com/launcher).
1. Search for "django certified by bitnami" and select the resulting `Django Certified by Bitnami` template.
1. Review the information and cost. Click `Launch on Compute Engine` to proceed.
1. Review the default zone, machine type, boot disk size and other parameters and modify as needed. Ensure that the `Allow HTTP traffic` and `Allow HTTPS traffic` boxes are checked in the firewall configuration. Click `Deploy` to proceed with the deployment.

The Cloud Launcher deploys Bitnami Django on a new Google Compute Engine instance. You can monitor the progress of the deployment from the [Deployment Manager](https://console.cloud.google.com/dm/deployments). Once deployed, note the public IP address of the instance and the password for the MySQL and PostgreSQL databases.

## Create a "hello world" Django application

Login to the deployed instance and create a simple Django application:

1. From the [Deployment Manager](https://console.cloud.google.com/dm/deployments), click the `SSH` button to login to the instance over SSH.
1. Once logged in, switch to the `bitnami` user account:

        sudo su - bitnami

1. Navigate to the default Django projects folder:

        cd /opt/bitnami/apps/django/django_projects

1. Create a new project using the command below:

        django-admin.py startproject myproject

1. Create a new application skeleton within the project:

        cd myproject
        python3 manage.py startapp helloworld

1. Edit the `/opt/bitnami/apps/django/django_projects/myproject/helloworld/views.py` file and add this content:

        from django.http import HttpResponse

        def index(request):
          return HttpResponse("Hello world!")

1. Create the `/opt/bitnami/apps/django/django_projects/myproject/helloworld/urls.py` file and add these lines to it:

        from django.conf.urls import url
        from . import views

        urlpatterns = [
            url(r'^$', views.index, name='index'),
        ]

1. Edit the `/opt/bitnami/apps/django/django_projects/myproject/myproject/urls.py` file and modify it to look like this:

        from django.conf.urls import url
        from django.urls import include
        
        urlpatterns = [
            url(r'^helloworld/', include('helloworld.urls')),
        ]

## Serve the application with Apache

Bitnami Django includes a pre-configured instance of the Apache Web server. Configure Apache to serve the application on the standard Web server port 80:

1. Edit the WSGI application script file at `/opt/bitnami/apps/django/django_projects/myproject/myproject/wsgi.py` and modify it to look like this:

    ```py
    import os
    import sys
    sys.path.append('/opt/bitnami/apps/django/django_projects/myproject')
    os.environ.setdefault("PYTHON_EGG_CACHE", "/opt/bitnami/apps/django/django_projects/myproject/egg_cache")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    ```

1. Create a `conf/` subdirectory in the project directory and create an Apache configuration file:

    ```sh
    mkdir /opt/bitnami/apps/django/django_projects/myproject/conf
    touch /opt/bitnami/apps/django/django_projects/myproject/conf/httpd-app.conf
    ```

1. Add the following Apache directives in the `/opt/bitnami/apps/django/django_projects/myproject/conf/httpd-app.conf` file:

        <IfDefine !IS_DJANGOSTACK_LOADED>
          Define IS_DJANGOSTACK_LOADED
          WSGIDaemonProcess wsgi-djangostack   processes=2 threads=15    display-name=%{GROUP}
        </IfDefine>

        <Directory "/opt/bitnami/apps/django/django_projects/myproject/myproject">
            Options +MultiViews
            AllowOverride All
            <IfVersion >= 2.3>
                Require all granted
            </IfVersion>

            WSGIProcessGroup wsgi-djangostack

            WSGIApplicationGroup %{GLOBAL}
        </Directory>

        Alias /myproject/static "/opt/bitnami/apps/django/lib/python3.6/site-packages/Django-2.0.2-py3.6.egg/django/contrib/admin/static"
        WSGIScriptAlias /myproject '/opt/bitnami/apps/django/django_projects/myproject/myproject/wsgi.py'

1. Add the line below to the `/opt/bitnami/apache2/conf/bitnami/bitnami-apps-prefix.conf` file:

        Include "/opt/bitnami/apps/django/django_projects/myproject/conf/httpd-app.conf"

1. Edit the `/opt/bitnami/apps/django/django_projects/myproject/myproject/settings.py` file and update the `ALLOWED_HOSTS` variable with the public IP address of your Google Compute Engine instance, as in the example below:

        ALLOWED_HOSTS = ['XX.XX.XX.XX', 'localhost', '127.0.0.1']

1. Restart the Apache server using the Bitnami control script:

        sudo /opt/bitnami/ctlscript.sh restart apache

Browse to `http://XX.XX.XX.XX/myproject/helloworld` and confirm that you see the output `Hello world!`.

If you see this output, your simple Django application is now deployed and operational. You can begin modifying it to suit your requirements.

## Configure a database (optional)

To configure a database for your application, modify the `/opt/bitnami/apps/django/django_projects/myproject/myproject/settings.py` file as shown below:

### MySQL

    DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'DATABASE-NAME',
          'HOST': '/opt/bitnami/mysql/tmp/mysql.sock',
          'PORT': '3306',
          'USER': 'USERNAME',
          'PASSWORD': 'PASSWORD'
      }
    }

### PostgreSQL

    DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql_psycopg2',
          'NAME': 'DATABASE-NAME',
          'HOST': '/opt/bitnami/postgresql',
          'PORT': '5432',
          'USER': 'USERNAME',
          'PASSWORD': 'PASSWORD'
      }
    }

### SQLite

    DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': 'PATH-TO-DATABASE-FILE'
      }
    }

## Cleaning up

After you have finished this tutorial, you can remove the resources you created on Google Cloud Platform so you aren't billed for them any longer. You can delete the resources individually, or delete the entire project.

### Deleting the project

Visit the [Resource Manager](https://console.cloud.google.com/cloud-resource-manager). Select the project you used for this tutorial and click `Delete`. Once deleted, you cannot reuse the project ID.

### Deleting individual resources

Navigate to the [Deployment Manager](https://console.cloud.google.com/dm/deployments). Find the deployment you used for this tutorial and click `Delete`.

## Next steps

Learn more about the topics discussed in this tutorial:

* [Bitnami Django documentation](https://docs.bitnami.com/google/infrastructure/django/)
* [Django documentation](https://docs.djangoproject.com/en/2.0/)
* [Django best practices](http://django-best-practices.readthedocs.io/en/latest/)
