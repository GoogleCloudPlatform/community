"""Hooks Submodule"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import falcon


def api_key():

    def hook(req, resp, params):
        key = req.get_param('api_key')
        if key is None:
            raise falcon.HTTPForbidden(
                description='API KEY is required')
    return hook
