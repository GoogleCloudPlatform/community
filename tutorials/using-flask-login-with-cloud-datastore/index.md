---
title: Using Flask-Login with Cloud Firestore in Datastore mode
description: Represent your Cloud Datastore entity with a Python class(ie a model) and use this for Flask-Login user management
author: komlasapaty
tags: Flask Framework, Python 3, Firestore in Datastore mode
date_published: 
---

In this tutorial, you implement user authentication using the popular Flask extension [Flask-Login](https://flask-login.readthedocs.io) and [**Firestore in Datastore mode**](https://cloud.google.com/datastore/docs/datastore-api-tutorial) as the database backend/backing store.

User authentication and user session management is a crucial component of most web applications.  
Flask-Login is a Flask extension that helps the developer to handle authentication and user session management.  
Flask-Login requires the user(ie application user) to be represented using a Python class with specific properties and methods provided.  

The above requirement of Flask-Login is straightforward when using a relational databases like MySQL or Postgres. 
Using an ORM toolkit like SQL-Alchemy, you can easily create a user model/class to represent a user in a relational database and then add the methods and properties required by Flask-Login.  

However, for a NoSQL database like Firestore in Datastore mode, the Flask-Login requirement poses a challenge since the use of models/classes do not directly apply.  

This tutorial will demonstrate how to use Flask-Login with Firestore in Datastore mode with the help of a little library; Datastore-Entity.  
This tutorial will demonstrate how to model your Firestore in Datastore mode entity as a Python class in order to conveniently use popular Python libraries like Flask-Login, WTForms etc

To represent our Datastore entity with a Python class, we will use a library called Datastore-Entity. Think of Datastore-Entity as an ORM-like library for Firestore in Datastore mode.  
_Disclaimer: I'm the author of datastore-entity library. No Google affiliation._  

# Requirements

-  [Python3.7](https://www.python.org/downloads/) 
-  [Flask](https://github.com/pallets/flask) 
-  [Flask-Login](https://flask-login.readthedocs.io) 
-  [Datastore-Entity](https://datastore-entity.readthedocs.io) 


## Prerequisites
- Basic familiarity with Flask and Flask-Login.
- Basic familiarity with App Engine and Firestore in Datastore mode.

This short tutorial does not show a full Flask application or the basic use of Firestore in Datastore mode.  
It is assumed the reader has basic familiarity with these.



## Step to
Setting up your local environment
Install required libraries
Map your user class(using UserMixin)
Implement Flask /login view endpoint


### Set Up Your Local Environment
Note: Projects that use the Datastore mode API require an active App Engine application.
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
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  
**Windows**
_With Powershell_
$env:GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  
_With Command Prompt_
set GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-acount-key.json"  

You are now ready to connect to your Firestore in Datastore mode.


### Install required libraries
```bash
pip install flask flask-login datastore-entity
```
**NOTE:** Installing datastore-entity installs the required client libraries for **Firestore in Datastore mode**


### Create your Flask user model


```python
from flask_login import UserMixin
from datastore_entity import DatastoreEntity, EntityValue
import datetime


class User(DatastoreEntity, UserMixin):
    username = EntityValue(None)
    password = EntityValue(None)
    status = EntityValue(1)
    date_created = EntityValue(datetime.datetime.utcnow())


```


```python
from flask import Flask

app = Flask(__main__)
app.secret_key = "development_key"  #not secure


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
```




Your flask login and logout views
```python
from flask_login import login_required, logout_user, login_user

@page.route("/login", methods=['GET','POST'])
def login():
    form = LoginForm(next=request.args.get('next'))
    
    if form.validate_on_submit():
        identity = request.form.get('username')
        password = request.form.get('password')
        user = User().get_object(identity)  #fetch user using the username

        if user and user.authenticated(password):  # authenticate user here

            if login_user(user, remember=True):

                #handle optionally redirecting to the next URL safely
                next_url = form.next.data
                if next_url:
                    return redirect(safe_next_url(next_url))
                
                return redirect(url_for('page.dashboard'))
            else:
                flash('This account is not active','error')

        else: #authentication failed
            flash('Login or password is incorrect','error')

    return render_template("page/login.html", form=form)


@page.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out", "success")
    return redirect(url_for('page.login'))
```

## Next Steps
The same approach can be used with popular libraries like WTForms where a database model is populated with the form values using ```form.populate_obj(model)


## Useful links
-  [Firestore in Datastore mode Documentation](https://cloud.google.com/datastore)
-  [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/)
-  [Flask-Login Documentation](https://flask-login.readthedocs.io) 
-  [Datastore-Entity Documentation](https://datastore-entity.readthedocs.io)
-  [Datastore-Entity on Github](https://github.com/komlasapaty/datastore-entity)
-  [Flask-Login Tutorial Using Postgres](https://hackersandslackers.com/flask-login-user-authentication)