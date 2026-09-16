import logging

import requests


SUPPORTED_HTTP_METHODS = {"GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"}
logger = logging.getLogger(__name__)


def invoke_http(url, method="GET", json=None, **kwargs):
    """Call a downstream service and return its JSON response envelope."""
    method = method.upper()
    if method not in SUPPORTED_HTTP_METHODS:
        return {"code": 400, "message": "Unsupported HTTP method."}

    kwargs.setdefault("timeout", 10)
    try:
        response = requests.request(method, url, json=json, **kwargs)
    except requests.RequestException:
        logger.exception("Downstream HTTP request failed")
        return {"code": 502, "message": "Downstream service unavailable."}

    if not 200 <= response.status_code < 300:
        return {"code": response.status_code, "message": "Downstream service returned an error."}

    try:
        return response.json() if response.content else {"code": response.status_code}
    except ValueError:
        logger.exception("Downstream service returned invalid JSON")
        return {"code": 502, "message": "Downstream service returned invalid JSON."}
