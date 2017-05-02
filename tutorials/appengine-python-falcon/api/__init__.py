"""API MODULE"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from api.middleware import AuthMiddleware
from api.resources import Resource

import falcon


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

app.add_route('/', Resource())
app.add_error_handler(Exception, generic_error_handler)
