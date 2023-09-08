from typing import List

from attr import define
from trendup_storage.models import StorageReference
from trendup_video.web_recorded_video import WebRecordedVideo

from src.objects import TrajPosition, CurveFunctionParameters, GetYFunctionParameters, \
    GetXFromTimeFunctionParameters, StrikeZoneRequest


@define
class TrajCalculateRequest:
    videos: List[WebRecordedVideo]
    mound_distance_cm: float
    trigger_timestamp: int
    strike_zone: StrikeZoneRequest


@define
class TrajCalculateResponse:
    isStrike: bool
    distanceFromCenter: float
    positionOnHomePlate: TrajPosition
    curveFunction: CurveFunctionParameters
    getYFunction: GetYFunctionParameters
    getXFromTimeFunction: GetXFromTimeFunctionParameters  # time - release time
    fullCurveImg: StorageReference
    releaseHeight: float
    releaseExtension: float
    flightDurationOfMillis: int

    releaseTimestamp: int
    curveMinTimestamp: int
    curveMaxTimestamp: int
