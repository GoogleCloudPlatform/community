""" API MODULE """

import json
import falcon

class QuoteResource(object):
    """TODO"""

    def on_get(self, req, resp):
        """Handles GET requests"""
        quote = {
            'quote': 'I\'ve always been more interested in the future than in the past.',
            'author': 'Grace Hopper'
        }

        resp.body = json.dumps(quote)


API = falcon.API()
API.add_route('/', QuoteResource())
