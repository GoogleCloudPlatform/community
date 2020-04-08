import logging

def handle_alert(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/0.12/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>.

        see: https://prometheus.io/docs/alerting/configuration/#webhook_config
    """
    request_json = request.get_json()
    if request_json:
      logging.info(request_json)
    else:
      logging.warn("no msg")
    return 'ok'