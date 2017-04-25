"""Resources Submodule"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging

from api.hooks import api_key

import falcon


class Resource(object):

    def on_get(self, req, resp):
        resource = {
            'id': 1,
            'name': 'Random Name'
        }
        resp.body = json.dumps(resource)
        resp.status = falcon.HTTP_200

    @falcon.before(api_key())
    def on_post(self, req, resp):
        logging.info('Creating new resource')
        resource = {
            'id': 1,
            'name': 'Random Name'
        }
        resp.body = json.dumps(resource)
        resp.status = falcon.HTTP_201
