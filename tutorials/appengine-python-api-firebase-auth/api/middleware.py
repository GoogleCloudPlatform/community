"""Middleware Submodule"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import falcon
from firebase_admin import auth


class AuthMiddleware(object):
    """."""

    def process_request(self, req, resp):
        auth_value = req.get_header('Authorization', None)
        if auth_value is None or len(auth_value.split(' ')) != 2 or not self._token_is_valid(req, auth_value.split(' ')[1]):
            raise falcon.HTTPUnauthorized(description='Unauthorized')

    def _token_is_valid(self, req, token):
        try:
            decoded_token = auth.verify_id_token(token)
            req.context['auth_user'] = decoded_token
        except Exception as e:
            return False
        if not decoded_token:
            return False
        return True
