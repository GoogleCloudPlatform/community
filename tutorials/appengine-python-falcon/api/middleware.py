"""Middleware Submodule"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import falcon


class AuthMiddleware(object):
    """."""

    def process_request(self, req, resp):
        token = req.get_header('Authorization')
        if token is None or not self._token_is_valid():
            raise falcon.HTTPUnauthorized(description='Auth token required')

    def _token_is_valid(self):
        return True  # You should do this better!
