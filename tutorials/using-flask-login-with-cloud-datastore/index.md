---
title: Using Flask-Login with Cloud Firestore in Datastore mode
description: Represent your Cloud Datastore entity with a Python class(ie a model) and use this for Flask-Login user management
author: komlasapaty
tags: Flask Framework, Python 3, Firestore in Datastore mode
date_published: 
---

In this tutorial, you implement user authentication using the popular Flask extension [Flask-Login](https://flask-login.readthedocs.io) and [**Firestore in Datastore mode**](https://cloud.google.com/datastore/docs/datastore-api-tutorial) as the database backend/backing store.

User authentication and user session management is a crucial component of most web applications.  
Flask-Login is a Flask extension that helps the developer to hanle authentication and user session management.  
Flask-Login requires the user to be represented using a Python class with specific properties and methods provided.  

The above requirement of Flask-Login is straightforward when using a relational databases like MySQL or Postgres. 
Using an ORM toolkit like SQL-Alchemy, you can easily create a user model/class to represent a user in a relational database and then add the methods and properties required by Flask-Login.  

However, for a NoSQL database like Firestore in Datastore mode, the Flask-Login requirement poses a challenge since the use of models/classes do not directly apply.  

This tutorial will demonstrate how to use Flask-Login with Firestore in Datastore mode with the help of a little library; Datastore-Entity.  

_Disclaimer: I'm the author of datastore-entity library. No Google affiliation._  

Datastore-Entity library lets you map your datastore entity using Python classes. Think of it as an ORM-like library for Firestore in Datastore mode.  

# Requirements

-  [Python3.7](https://www.python.org/downloads/) 
-  [Flask](https://github.com/pallets/flask) 
-  [Flask-Login](https://flask-login.readthedocs.io) 
-  [Datastore-Entity](https://datastore-entity.readthedocs.io) 


## Prerequisites

Familiarity with Flask and Flask-Login
Familiarity with App Engine and Firestore in Datastore mode.
An active App Engine application (Projects that use the Datastore mode API require an active App Engine application.)   


## Step to

Install required libraries
Map your user class(using UserMixin)
Implement /login view endpoint



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