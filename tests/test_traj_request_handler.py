import json

import attrs
from tornado.web import Application
from trendup_storage.models import StorageReference
from trendup_video.web_recorded_video import WebRecordedVideo

from src.objects import StrikeZoneRequest
from src.web.models import TrajCalculateRequest
from src.web.traj_request_handler import TrajRequestHandler
from tests.base import TornadoTestCase
from tests.doubles.traj_calculate_controller import TrajCalculateControllerMock
from tests.web_stubs import WebStubs


class TestTrajRequestHandler(TornadoTestCase):

    def setUp(self) -> None:
        self.controller = TrajCalculateControllerMock()
        super().setUp()

    def get_app(self) -> Application:
        return Application([
            (r"/", TrajRequestHandler, {"controller": self.controller})
        ])

    def test_without_body_should_400(self):
        self.assertMissingBodyField({})
        self.assertMissingBodyField({
            "triggerTimestamp": 1000,
        })

    def test_should_return_200_with_null_if_controller_returns_none(self):
        self.controller.add_mock_response(self._get_sample_request(), None)
        response = self.fetch("/", method="POST", body=json.dumps(self._get_sample_json_body()))
        self.assertEqual(response.code, 204)

    def test_should_call_controller_with_object_deserialized(self):
        res = WebStubs.traj_calculate_response()
        self.controller.add_mock_response(
            request=self._get_sample_request(),
            response=res
        )
        response = self.fetch("/", method="POST", body=json.dumps(self._get_sample_json_body()))
        self.assertEqual(response.code, 200)
        self.assertBodyJson(response, attrs.asdict(res))

    def assertMissingBodyField(self, body):
        response = self.fetch("/", method="POST", body=json.dumps(body))
        self.assertEqual(response.code, 400)

    def _get_sample_json_body(self) -> dict:
        return {
            "videos": [
                {
                    "recorderName": "test",
                    "storageReference": {
                        "env": "LOCAL",
                        "id": "123"
                    },
                    "timestamps": [1, 2, 3],
                }
            ],
            "triggerTimestamp": 1000,
            "strikeZone": {
                "lowCm": 100,
                "highCm": 200,
            },
            "moundDistanceCm": 27,
        }

    def _get_sample_request(self) -> TrajCalculateRequest:
        return TrajCalculateRequest(
            videos=[WebRecordedVideo(
                recorder_name="test",
                storage_reference=StorageReference(
                    env="LOCAL",
                    id="123"
                ),
                timestamps=[1, 2, 3]
            )],
            trigger_timestamp=1000,
            strike_zone=StrikeZoneRequest(
                low_cm=100,
                high_cm=200,
            ),
            mound_distance_cm=27
        )
