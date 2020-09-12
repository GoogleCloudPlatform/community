---
title: Using Flask-Login with Cloud Firestore in Datastore mode
description: Represent your Cloud Datastore entity with a Python class and use this for Flask-Login user management.
author: komlasapaty
tags: Flask Framework, Python 3
date_published: 2020-9-15
---

In this tutorial, you will implement user authentication using the popular Flask extension [Flask-Login](https://flask-login.readthedocs.io) with [**Firestore in Datastore mode**](https://cloud.google.com/datastore/docs/datastore-api-tutorial) as the database backend.


## Prerequisites
This tutorial is not to teach the fundamentals of Flask-Login or Firestore in Datastore mode. It is to demonstrate the use of Firestore in Datastore mode(as opposed to any relational database) as the database backend for user authentication with Flask-Login.  
The use of Flask-Login should not force you to abandon the power of Firestore in Datastore mode in favour of a relational database.

Basic familiarity with the following is assumed:
- Flask and Flask-Login.
- App Engine and Firestore in Datastore mode.

## Requirements

-  [Python3.7](https://www.python.org/downloads/) 
-  [Flask](https://github.com/pallets/flask) 
-  [Flask-Login](https://flask-login.readthedocs.io) 
-  [Datastore-Entity](https://datastore-entity.readthedocs.io)  


## Introduction
Flask-Login **requires** the user(ie application user) to be represented using a Python class with specific properties and methods provided.  

The above requirement of Flask-Login is straightforward when using a relational database such as MySQL or Postgres.  
Using an ORM toolkit like SQL-Alchemy, you can easily create a user model/class to represent a user in a relational database.  
Methods and properties required by Flask-Login can then be added to the user model.

However, for a NoSQL database like Firestore in Datastore mode, this Flask-Login requirement poses a challenge.  
This is because the pattern of using a model/class to represent a database record does not directly apply.  



This tutorial will demonstrate how to model your Firestore in Datastore mode entity as a Python class.  
This will let you conveniently use popular Python libraries like **Flask-Login**, **WTForms** etc.  

To model our Datastore entity as a Python class, we will use **Datastore-Entity** library.  
Think of Datastore-Entity as an _ORM-like_ library for Firestore in Datastore mode.  
_Disclaimer: I'm the author of datastore-entity. No Google affiliation._  


### Set up your local environment
NOTE: Projects that use the Datastore mode API require an active App Engine application.
So you should already have App Engine and Datastore mode API enabled in your GCP project.  

As usual, to connect to your Google Cloud service from your local machine you need the appropriate credentials(service account key).  
_Create and download service account key_
- On the GCP console, go to **Main menu** -> **IAM & Admin** -> click **Service Account** on the left pane -> click **CREATE SERVICE ACCOUNT** at the top. 
- Give the service account an appropriate name (eg. datastore-service-account). Enter an optional description below and click **CREATE**
- Under **Select a role** dropdown menu, type **Cloud Datastore owner** in the filter field, select it and click **CONTINUE** and click **DONE** on the next page.
- On the **Service Account** page, look for the service account you just created and click the overflow icon (vertical ellipsis) at the far right end.
- Click **Create Key**  from the dropdown menu and make sure **JSON** is selected as the **Key type**.
- Click **CREATE**. This automatically downloads the service account JSON key to your local machine. Take note of the file name on the popup screen.


_Configure your service account on your local machine_  
Point the environment variable **GOOGLE_APPLICATION_CREDENTIALS** to the location of the service account key you downloaded.  
**Linux/maxOS**  
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  
```
**Windows**  
_With Powershell_  
```
$env:GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  
```
_With Command Prompt_  
```
set GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  
```
You are now ready to connect to your Firestore in Datastore mode.


### Install required libraries
```bash
pip install flask flask-login datastore-entity
```
NOTE: Installing datastore-entity installs the required/official client library for **Firestore in Datastore mode.**

### Create your Flask user model
Model your ```user``` entity.

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

### Implement the Flask 'login' view
Once the entity is modelled, you can fetch your user entity using familiar ORM pattern.  
Use the methods provided on your model to fetch the user record.  

An example flask login view.  
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
        user = User().get_object('username',identity)

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
### Conclusion
You can employ same approach to model any other Firestore in Datastore mode entity to persist/update data.
This technique can let Firestore in Datastore mode be a drop-in replacement for your relational database with little to no code changes.


## Useful links
-  [Firestore in Datastore mode Documentation](https://cloud.google.com/datastore)
-  [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/)
-  [Flask-Login Documentation](https://flask-login.readthedocs.io) 
-  [Datastore-Entity Documentation](https://datastore-entity.readthedocs.io)
-  [Flask-Login Tutorial Using Postgres](https://hackersandslackers.com/flask-login-user-authentication)
