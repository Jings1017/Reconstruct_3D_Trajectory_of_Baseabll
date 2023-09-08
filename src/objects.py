from typing import List

from attrs import define
from trendup_video.recorded_video import RecordedVideo
from trendup_video.type_alias import Frame


@define
class TrajCalculateMaterials:
    videos: List[RecordedVideo]
    trigger_timestamp: int
    mound_distance_cm: float
    strike_zone: 'StrikeZoneRequest'

    def find_video(self, recorder_name: str) -> RecordedVideo:
        return next(filter(lambda v: v.recorder_name == recorder_name, self.videos))


@define
class StrikeZoneRequest:
    low_cm: float
    high_cm: float


@define
class TrajPosition:
    x: float
    y: float
    z: float
    timestamp: float


@define
class VideoData:
    path: str
    timestamps: List[float]


@define
class ReferenceObject:
    length: float
    width: float
    height: float
    distance_x: float
    altitude: float


@define
class TrajCalculateResult:
    is_strike: bool
    is_land_early: bool
    distance_from_center: float
    position_on_home_plate: 'TrajPosition'
    curve_function: 'CurveFunctionParameters'
    get_y_function: 'GetYFunctionParameters'
    get_x_from_time_function: 'GetXFromTimeFunctionParameters'  # time - release time
    full_curve_img: Frame
    release_height: float
    release_extension: float
    flight_duration_of_millis: int

    release_timestamp: int
    curve_min_timestamp: int
    curve_max_timestamp: int


@define
class CurveFunctionParameters:
    a: float
    b: float
    c: float
    d: float
    e: float


@define
class GetYFunctionParameters:
    a: float
    b: float
    c: float


@define
class GetXFromTimeFunctionParameters:
    a: float
    b: float
