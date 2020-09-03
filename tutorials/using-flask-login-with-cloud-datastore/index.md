---
title: Using Flask-Login with Cloud Firestore in Datastore mode
description: Represent your Cloud Datastore entity with a Python class(ie a model) and use this for Flask-Login user management
author: komlasapaty
tags: Flask Framework, Python 3, Firestore in Datastore mode
date_published: 
---

In this tutorial, you implement user authentication using the popular Flask extension [Flask-Login](https://flask-login.readthedocs.io) and [**Firestore in Datastore mode**](https://cloud.google.com/datastore/docs/datastore-api-tutorial) as the database backend.

User authentication and user session management is a crucial component of most web applications.
Flask-Login is a Flask extension that helps the developer to authenticate and manage user session. 
Flask-Login requires the user to be represented using a Python class with specific properties and methods provided.

The above requirement of Flask-Login is straightforward when using a relational database like MySQL or Postgres. 
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


##Prerequisites
Familiarity with Flask and Flask-Login
Familiarity with App Engine and Firestore in Datastore mode.
An active App Engine application (Projects that use the Datastore mode API require an active App Engine application.)   


##Step to 
Install the libraries
Map your user class(using UserMixin)
Implement /login view endpoint


#Next Steps
The same approach can be used with populare libraries like WTForms etc.


# Useful links
-  [Firestore in Datastore mode Documentation](https://cloud.google.com/datastore)
-  [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/)
-  [Flask-Login Documentation](https://flask-login.readthedocs.io) 
-  [Datastore-Entity Documentation](https://datastore-entity.readthedocs.io)
-  [Datastore-Entity on Github](https://github.com/komlasapaty/datastore-entity)
-  [Flask-Login Tutorial Using Postgres](https://hackersandslackers.com/flask-login-user-authentication)