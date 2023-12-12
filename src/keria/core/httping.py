# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.httping module

"""

import falcon
import re
from falcon.http_status import HTTPStatus
from typing import Callable


def cors_config(config: str):
    """
    Configuration for HandleCORS middleware
    """
    if config is None or config.strip() == "":
        return lambda _: True
    if config.lower() == "true" or config == "1":
        return lambda _: True
    if config.lower() == "false" or config == "0":
        return lambda _: False
    return lambda origin: re.match(config, origin) is not None


ORIGIN = "Origin"
ALLOW_ORIGIN = "Access-Control-Allow-Origin"
REQUEST_METHOD = "Access-Control-Request-Method"
ALLOW_METHODS = "Access-Control-Allow-Methods"
REQUEST_HEADERS = "Access-Control-Request-Headers"
ALLOW_HEADERS = "Access-Control-Allow-Headers"
REQUEST_PRIVATE_NETWORK = "Access-Control-Request-Private-Network"
ALLOW_PRIVATE_NETWORK = "Access-Control-Allow-Private-Network"
EXPOSE_HEADERS = "Access-Control-Expose-Headers"
MAX_AGE = "Access-Control-Max-Age"
ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"


class HandleCORS(object):
    """
    Falcon middleware to implement Cross-Origin Resource Sharing (CORS)

    See also:
        https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
    See also:
        https://developer.chrome.com/blog/private-network-access-preflight/
    """

    def __init__(self, isallowed: Callable[[str], bool] = None):
        self.isallowed = isallowed
        pass

    def process_request(self, req, resp):

        # Origin
        origin = req.get_header(ORIGIN)
        # This is not a CORS request, do nothing
        if origin is None:
            return
        # Use callback to check origin permission. If denied then do nothing
        if (self.isallowed is not None) and (self.isallowed(origin) is not True):
            return
        resp.set_header(ALLOW_ORIGIN, origin)

        # Request-Method
        requestMethod = req.get_header(REQUEST_METHOD)
        if requestMethod is not None:
            resp.set_header(ALLOW_METHODS, requestMethod)

        # Request-Headers
        requesHeaders = req.get_header(REQUEST_HEADERS)
        if requesHeaders is not None:
            resp.set_header(ALLOW_HEADERS, requesHeaders)

        # Request-Private-Network (chrome)
        # https://developer.chrome.com/blog/private-network-access-preflight/
        privateNetwork = req.get_header(REQUEST_PRIVATE_NETWORK)
        if privateNetwork == 'true':
            resp.set_header(ALLOW_PRIVATE_NETWORK, privateNetwork)

        # Expose-Headers
        resp.set_header(EXPOSE_HEADERS, '*')

        # Max-Age
        resp.set_header(MAX_AGE, 5*60)  # 5 minutes

        # Allow-Credentials - make sure this is not set
        resp.delete_header(ALLOW_CREDENTIALS)

        # This is a CORS pre-flight request, return empty 204 response
        if req.method == 'OPTIONS' and requestMethod is not None:
            raise HTTPStatus(falcon.HTTP_204, body='')


def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(
            description=f"required field '{name}' missing from request")

    return param


def parseRangeHeader(header, name, start=0, end=9):
    """ Parse the start and end requested range values, defaults are 0, 9

    Parameters:
        header(str):  HTTP Range header value
        name (str): range name to look for
        start (int): default start index
        end(int): default end index

    Returns:
        (start, end): tuple of start index and end index

    """

    if not header.startswith(f"{name}="):
        return start, end

    header = header.strip(f"{name}=")
    try:
        if header.startswith("-"):
            return start, int(header[1:])

        if header.endswith("-"):
            return int(header[:-1]), end

        vals = header.split("-")
        if not len(vals) == 2:
            return start, end

        return int(vals[0]), int(vals[1])
    except ValueError:
        return start, end
