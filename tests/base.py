import json

from tornado.testing import AsyncHTTPTestCase


class TornadoTestCase(AsyncHTTPTestCase):

    def assertBodyJson(self, response, expected: dict):
        self.assertDictEqual(json.loads(response.body.decode()), expected)

    def assertBody(self, response, expected: str):
        self.assertEqual(response.body.decode(), expected)
