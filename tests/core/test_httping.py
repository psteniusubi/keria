import unittest
from falcon import falcon
from falcon.testing import helpers
from falcon.http_status import HTTPStatus
from keria.core.httping import HandleCORS, cors_config

"""
Using curl to test CORS config

Pre-flight request with CORS enabled for given Origin produces response 
where Access-Control-Allow-Origin and other CORS response headers are set.

curl -i -X OPTIONS http://localhost:3901 -H "Origin: https://example.com" -H "Access-Control-Request-Method: GET"

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET
Access-Control-Expose-Headers: *
Access-Control-Max-Age: 300

Pre-flight request with CORS disabled produces response where no CORS response headers are set.

curl -i -X OPTIONS http://localhost:3901 -H "Origin: https://example.com" -H "Access-Control-Request-Method: GET"

HTTP/1.1 401 Unauthorized
Content-Length: 0
Content-Type: application/json
"""

TEST_ORIGIN = "https://localhost"


class HandleCORSTest(unittest.TestCase):
    def isallowed(self, origin):
        if origin == TEST_ORIGIN:
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
            "Origin": TEST_ORIGIN,
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
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Origin'),
            TEST_ORIGIN)
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Methods'),
            "GET")
        self.assertEqual(
            resp.get_header('Access-Control-Expose-Headers'),
            "*")
        self.assertEqual(
            resp.get_header('Access-Control-Max-Age'),
            "300")

    def test_cors_headers(self):
        headers = {
            "Origin": TEST_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(len(resp.headers), 5)
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Origin'),
            TEST_ORIGIN)
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Methods'),
            "GET")
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Headers'),
            "content-type")
        self.assertEqual(
            resp.get_header('Access-Control-Expose-Headers'),
            "*")
        self.assertEqual(
            resp.get_header('Access-Control-Max-Age'),
            "300")

    def test_cors_private_network(self):
        headers = {
            "Origin": TEST_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Private-Network": "true"
        }
        req = helpers.create_req(method='GET', headers=headers)
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(len(resp.headers), 5)
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Origin'),
            TEST_ORIGIN)
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Methods'),
            "GET")
        self.assertEqual(
            resp.get_header('Access-Control-Allow-Private-Network'),
            "true")
        self.assertEqual(
            resp.get_header('Access-Control-Expose-Headers'),
            "*")
        self.assertEqual(
            resp.get_header('Access-Control-Max-Age'),
            "300")

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

    def test_cors_config(self):
        # config None
        fn = cors_config(None)
        self.assertTrue(fn("https://example.com"))
        self.assertTrue(fn("https://localhost"))
        # config ""
        fn = cors_config("")
        self.assertTrue(fn("https://example.com"))
        self.assertTrue(fn("https://localhost"))
        # config "true"
        fn = cors_config("true")
        self.assertTrue(fn("https://example.com"))
        self.assertTrue(fn("https://localhost"))
        # config "1"
        fn = cors_config("1")
        self.assertTrue(fn("https://example.com"))
        self.assertTrue(fn("https://localhost"))
        # config "false"
        fn = cors_config("false")
        self.assertFalse(fn("https://example.com"))
        self.assertFalse(fn("https://localhost"))
        # config "0"
        fn = cors_config("0")
        self.assertFalse(fn("https://example.com"))
        self.assertFalse(fn("https://localhost"))
        # config regex pattern
        fn = cors_config("^(https://localhost)|(https://test)$")
        self.assertFalse(fn("https://example.com"))
        self.assertTrue(fn("https://localhost"))
        self.assertTrue(fn("https://test"))
