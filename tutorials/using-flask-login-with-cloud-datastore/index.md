---
title: Using Flask-Login with Firestore in Datastore mode
description: Represent your Datastore entity with a Python class and use this for Flask-Login user management.
author: komlasapaty
tags: Flask Framework, Python 3
date_published: 2020-09-25
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you implement user authentication using the popular Flask extension [Flask-Login](https://flask-login.readthedocs.io) with
[Firestore in Datastore mode](https://cloud.google.com/datastore/docs/datastore-api-tutorial) as the database backend. This tutorial demonstrates the use of 
Firestore in Datastore mode (as opposed to any relational database) as the database backend for user authentication with Flask-Login.

The use of Flask-Login should not force you to abandon the power of Firestore in Datastore mode in favor of a relational database.

This tutorial doesn't teach the fundamentals of Flask-Login or Firestore in Datastore mode.

Basic familiarity with the following is assumed:

- Flask
- Flask-Login
- App Engine
- Firestore in Datastore mode

## Requirements

-  [Python3.7](https://www.python.org/downloads/) 
-  [Flask](https://github.com/pallets/flask) 
-  [Flask-Login](https://flask-login.readthedocs.io) 
-  [Datastore Entity](https://datastore-entity.readthedocs.io)  

## Introduction

Flask-Login requires the user (that is, the application user) to be represented using a Python class with specific properties and methods provided. This 
requirement of Flask-Login is straightforward when using a relational database such as MySQL or Postgres. Using an ORM toolkit like SQL-Alchemy, you can easily 
create a user model/class to represent a user in a relational database. Methods and properties required by Flask-Login can then be added to the user model.

However, for a NoSQL database like Firestore in Datastore mode, this Flask-Login requirement poses a challenge, because the pattern of using a model/class to 
represent a database record does not directly apply.  

This tutorial demonstrates how to model your Firestore in Datastore mode entity as a Python class, which lets you use popular Python libraries like 
Flask-Login and WTForms.  

To model a Datastore entity as a Python class, this tutorial uses the [Datastore Entity library](https://datastore-entity.readthedocs.io). Think of Datastore 
Entity as an ORM-like library for Firestore in Datastore mode. 

The author of this tutorial is also the author of the Datastore Entity library.  

## Set up your local environment

Projects that use the Datastore mode API require an active App Engine application, so you should already have the App Engine and Datastore mode APIs enabled in
your Google Cloud project.  

### Create and download service account key

To connect to your Google Cloud service from your local machine, you need the appropriate credentials (service account key).

1.  In the Cloud Console, go to the [**Service accounts** page](https://console.cloud.google.com/iam-admin/serviceaccounts).
1.  Click **Create service account**.
1.  Give the service account an appropriate name, such as `datastore-service-account`, enter a description, and click **Create**.
1.  Under **Select a role**, type `Cloud Datastore Owner` in the filter field, select **Cloud Datastore Owner**, click **Continue**, and click **Done**.
1.  On the **Service accounts** page, look for the service account that you just created, click the button at the far right end of the row in the
    **Actions** column, and select **Create key** in the dropdown menu. 
1.  Make sure that **JSON** is selected as the **Key type**, and click **Create**.

    This automatically downloads the service account JSON key to your local machine. Take note of the filename.

### Configure your service account on your local machine

Point the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the location of the service account key you downloaded:

*   Linux or macOS:

        export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

*   Windows, with Powershell:

        $env:GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

*   Windows, with Command Prompt:

        set GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"  

You are now ready to connect to your Firestore in Datastore mode.

### Install required libraries

Run the following command to install the required libraries:

    pip install flask flask-login datastore-entity

Installing `datastore-entity` installs the required official client library for Firestore in Datastore mode.

## Create your Flask user model

Model your `user` entity.

```python
from flask_login import UserMixin
from datastore_entity import DatastoreEntity, EntityValue
import datetime


class User(DatastoreEntity, UserMixin):
    username = EntityValue(None)
    password = EntityValue(None)
    status = EntityValue(1)
    date_created = EntityValue(datetime.datetime.utcnow())

    # other fields or methods go here...
    #def authenticated(self, password):
    #    ...
```

## Implement the Flask login view

After the entity is modeled, you can fetch your user entity using familiar ORM patterns.

Use the methods provided on your model to fetch the user record.

An example Flask-Login view:

```python
from flask_login import login_user
from models import User

@page.route("/login", methods=['GET','POST'])
def login():
    form = LoginForm(next=request.args.get('next'))
    
    if form.validate_on_submit():
        identity = request.form.get('username')
        password = request.form.get('password')

        # fetch user using the 'username' property
        # refer to the datastore-entity documentation for more
        user = User().get_obj('username',identity)

        if user and user.authenticated(password):

            if login_user(user, remember=True):
                user.update_activity()

                #handle optionally redirecting to the next URL safely
                next_url = form.next.data
                if next_url:
                    return redirect(safe_next_url(next_url))
                
                return redirect(url_for('page/dashboard.html'))
            else:
                flash('This account is not active','error')

        else: 
            flash('Login or password is incorrect','error')

    return render_template("page/login.html", form=form)
```

## Conclusion

You can employ the same approach to model any other Firestore in Datastore mode entity to persist and update data.

This technique can let Firestore in Datastore mode be a drop-in replacement for your relational database with little to no code change.


## What's next

-  [Firestore in Datastore mode documentation](https://cloud.google.com/datastore)
-  [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/)
-  [Flask-Login documentation](https://flask-login.readthedocs.io) 
-  [Datastore Entity documentation](https://datastore-entity.readthedocs.io)
-  [Flask-Login tutorial using Postgres](https://hackersandslackers.com/flask-login-user-authentication)
