import unittest
from falcon import falcon
from falcon.testing import helpers
from falcon.http_status import HTTPStatus
from keria.core.httping import HandleCORS

ORIGIN = "https://localhost"


class HandleCORSTest(unittest.TestCase):
    def isallowed(self, origin):
        if origin == ORIGIN:
            return True
        return False
    
    def setUp(self):
        self.cors_handler = HandleCORS(isallowed=self.isallowed)

    def test_not_cors(self):
        headers = dict()
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        # no headers were set
        self.assertEqual(len(resp.headers), 0)

    def test_cors_preflight(self):
        headers = {
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET"
        }
        req = helpers.create_req(method='OPTIONS', headers=headers)
        resp = falcon.Response()

        with self.assertRaises(HTTPStatus) as cm:
            self.cors_handler.process_request(req, resp)

        # status 204 with empty body
        self.assertEqual(cm.exception.status, falcon.HTTP_204)
        self.assertEqual(cm.exception.text, "")

        self.assertEqual(len(resp.headers), 4)
        self.assertEqual(resp.get_header('Access-Control-Allow-Origin'), ORIGIN)
        self.assertEqual(resp.get_header('Access-Control-Allow-Methods'), "GET")
        self.assertEqual(resp.get_header('Access-Control-Expose-Headers'), "*")
        self.assertEqual(resp.get_header('Access-Control-Max-Age'), "300")

    def test_cors_headers(self):
        headers = {
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(len(resp.headers), 5)
        self.assertEqual(resp.get_header('Access-Control-Allow-Origin'), ORIGIN)
        self.assertEqual(resp.get_header('Access-Control-Allow-Methods'), "GET")
        self.assertEqual(resp.get_header('Access-Control-Allow-Headers'), "content-type")
        self.assertEqual(resp.get_header('Access-Control-Expose-Headers'), "*")
        self.assertEqual(resp.get_header('Access-Control-Max-Age'), "300")

    def test_cors_private_network(self):
        headers = {
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Private-Network": "true"
        }
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(len(resp.headers), 5)
        self.assertEqual(resp.get_header('Access-Control-Allow-Origin'), ORIGIN)
        self.assertEqual(resp.get_header('Access-Control-Allow-Methods'), "GET")
        self.assertEqual(resp.get_header('Access-Control-Allow-Private-Network'), "true")
        self.assertEqual(resp.get_header('Access-Control-Expose-Headers'), "*")
        self.assertEqual(resp.get_header('Access-Control-Max-Age'), "300")

    def test_origin_not_allowed(self):
        headers = {
            "Origin": "https://example",
            "Access-Control-Request-Method": "GET"
        }
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        # no headers were set
        self.assertEqual(len(resp.headers), 0)
