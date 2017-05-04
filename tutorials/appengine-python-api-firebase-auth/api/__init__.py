"""API MODULE"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import logging

from api.middleware import AuthMiddleware
from api.resources import Resource

import falcon
import firebase_admin


def generic_error_handler(ex, req, resp, params):

    if isinstance(ex, falcon.HTTPNotFound):
        raise falcon.HTTPNotFound(description='Not Found')
    elif isinstance(ex, falcon.HTTPMethodNotAllowed):
        raise falcon.HTTPMethodNotAllowed(falcon.HTTP_405, description='Method Not Allowed')
    else:
        raise


app = falcon.API(middleware=[
    AuthMiddleware()
])

# JWT using Firebase Auth
default_app = firebase_admin.initialize_app()

app.add_route('/', Resource())
app.add_error_handler(Exception, generic_error_handler)
