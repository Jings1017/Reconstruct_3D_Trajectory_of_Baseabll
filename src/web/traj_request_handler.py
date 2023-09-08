from typing import List

import attrs
from trendup_storage.models import StorageReference
from trendup_video.web_recorded_video import WebRecordedVideo

from src.objects import StrikeZoneRequest
from src.web.json_request_handler import JsonRequestHandler
from src.web.models import TrajCalculateRequest
from src.web.traj_calculate_controller import TrajCalculateController


class TrajRequestHandler(JsonRequestHandler):

    def initialize(self, controller: TrajCalculateController):
        self.controller = controller

    def post(self):
        body = self.decode_body()
        timestamp = self.get_timestamp(body)
        videos = self._grab_videos_from_body(body)
        mound_distance = self._get_mound_distance(body)
        zone = self._get_strike_zone(body)

        result = self.controller.calculate(TrajCalculateRequest(
            videos=videos,
            trigger_timestamp=timestamp,
            strike_zone=zone,
            mound_distance_cm=mound_distance
        ))

        if result is None:
            self.set_status(204)
        else:
            self.write(attrs.asdict(result))

    def get_timestamp(self, body):
        timestamp = body.get("triggerTimestamp")

        if timestamp is None:
            self.error(400, "Missing triggerTimestamp field")

        return timestamp

    def _grab_videos_from_body(self, body: dict) -> List[WebRecordedVideo]:
        videos_raw = body.get("videos")

        if videos_raw is None:
            self.error(400, "Missing videos field")

        try:
            return [WebRecordedVideo(
                recorder_name=video["recorderName"],
                storage_reference=StorageReference(**video["storageReference"]),
                timestamps=video["timestamps"]
            ) for video in videos_raw]
        except Exception as e:
            self.error(400, "Invalid video format")

    def _get_mound_distance(self, body: dict) -> float:
        mound_distance = body.get("moundDistanceCm")

        if mound_distance is None:
            self.error(400, "Missing moundDistance field")

        return mound_distance

    def _get_strike_zone(self, body: dict) -> StrikeZoneRequest:
        strike_zone_raw = body.get("strikeZone")

        if strike_zone_raw is None:
            self.error(400, "Missing strikeZone field")

        try:
            return StrikeZoneRequest(
                low_cm=strike_zone_raw["lowCm"],
                high_cm=strike_zone_raw["highCm"]
            )
        except Exception as e:
            self.error(400, "Invalid strike zone format")
