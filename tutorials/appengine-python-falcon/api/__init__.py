"""API MODULE"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from api.middleware import AuthMiddleware
from api.resources import Resource

import falcon


app = falcon.API(middleware=[
    AuthMiddleware()
])

resource = Resource()
app.add_route('/', resource)
