---
title: Using System V shared memory on the App Engine flexible environment PHP runtime
description: Learn how to use System V shared memory in a PHP App Engine flexible environment app.
author: tmatsuo
tags: App Engine, PHP
date_published: 2017-01-23
---

Takashi Matsuo | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

PHP has a wrapper for the System V IPC family of functions including
semaphores, shared memory, and inter-process messaging. For more
details, visit
[the official documentation](http://php.net/manual/en/intro.sem.php).

[Our PHP runtime](https://github.com/googlecloudplatform/php-docker)
provides these features out of the box, so you can immediately start
using them on [App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/).
We'll walk through a small demo app to learn how to use them.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Simple counter with the shared memory

1. Create a directory

        mkdir myapp
        cd myapp

1. Create an `app.yaml` file:

        runtime: php
        env: flex

        manual_scaling:
            instances: 1

1. Create an `index.php` file:

        <?php

        # Obtain an exclusive lock
        $key = ftok(__FILE__, 'p');
        $semid = sem_get($key);
        sem_acquire($semid);

        # Attach shared memory
        $id = shm_attach($key);

        # Count up
        if (shm_has_var($id, 0)) {
            $count = shm_get_var($id, 0) + 1;
        } else {
            $count = 1;
        }

        # Save the value
        shm_put_var($id, 0, $count);

        shm_detach($id);

        # Release the lock
        sem_release($semid);
        echo sprintf("%d visits so far", $count);

1. Deploy the app:

        gcloud app deploy app.yaml

1. Access the app and see the counts. For example, you can use `ab`:

        ab -n100 -c10 http://your-project-id.appspot-preview.com/

   Access the same URL with a browser to see the counter.

## Caveats

This counter application is not for production use at all. The shared
memory is not shared among multiple servers, and also the memory will
go away when the server restarts. It only demonstrates how they work.

## Next step

1. Learn more about [System V IPC family](http://php.net/manual/en/intro.sem.php)
