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
current = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.abspath(os.path.join(current, 'config/serviceAccount.json'))
cred = firebase_admin.credentials.Certificate(file_path)

default_app = firebase_admin.initialize_app(cred)

custom_token = firebase_admin.auth.create_custom_token('WvA0NQs8tFSkZkGXR6CrnNhEDz82')
logging.info('TOKEN: ' + custom_token)


app.add_route('/', Resource())
app.add_error_handler(Exception, generic_error_handler)
