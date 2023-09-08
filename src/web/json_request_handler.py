import json

import tornado.escape
from tornado.web import RequestHandler


class JsonRequestHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, PATCH, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Expose-Headers", "*")

    def check_body(self, *required_keys: str):
        body = self.decode_body()

        for key in required_keys:
            if key not in body:
                self.throw_bad_request(f"Missing {key}")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def throw_bad_request(self, message: str):
        self.error(400, message)

    def error(self, status: int, message: str):
        raise tornado.web.HTTPError(status, message)

    def decode_body(self):
        return tornado.escape.json_decode(self.request.body)

    def write_error(self, status_code, **kwargs):
        error_type, error, traceback = kwargs["exc_info"]

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"error": str(error.log_message)}))
