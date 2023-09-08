from trendup_storage.models import StorageReference
from trendup_video.web_recorded_video import WebRecordedVideo

from src.web.models import TrajCalculateResponse
from tests.stubs import Stubs


class WebStubs:

    @staticmethod
    def traj_calculate_response() -> TrajCalculateResponse:
        return TrajCalculateResponse(
            isStrike=True,
            distanceFromCenter=1.0,
            positionOnHomePlate=Stubs.traj_position(),
            curveFunction=Stubs.curve_fun_params(),
            getYFunction=Stubs.get_y_fun_params(),
            getXFromTimeFunction=Stubs.get_x_from_time_fun_params(),
            fullCurveImg=StorageReference(env="LOCAL", id="123"),
            releaseHeight=2.0,
            flightDurationOfMillis=1000,
            releaseTimestamp=2000,
            curveMinTimestamp=3000,
            curveMaxTimestamp=4000,
            releaseExtension=5000,
        )

    @staticmethod
    def recorded_video() -> WebRecordedVideo:
        return WebRecordedVideo(
            recorder_name="test",
            storage_reference=StorageReference(
                env="LOCAL",
                id="123"
            ),
            timestamps=[1, 2, 3]
        )
