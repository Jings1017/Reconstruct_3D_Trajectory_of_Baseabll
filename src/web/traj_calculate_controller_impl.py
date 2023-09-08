from typing import Optional

from attr import define
from trendup_storage.image.image_storage import ImageStorage
from trendup_video.web.pre_handle_video import PreHandleVideo

from src.objects import TrajCalculateMaterials
from src.traj_calculator import TrajCalculator
from src.web.models import TrajCalculateRequest, TrajCalculateResponse
from src.web.traj_calculate_controller import TrajCalculateController


@define
class TrajCalculateControllerImpl(TrajCalculateController):
    pre_handle_video: PreHandleVideo
    traj_calculator: TrajCalculator
    image_storage: ImageStorage

    def calculate(self, request: TrajCalculateRequest) -> Optional[TrajCalculateResponse]:
        videos = self.pre_handle_video.pre_handle_video(request.videos)
        result = self.traj_calculator.calculate(TrajCalculateMaterials(
            videos=videos,
            trigger_timestamp=request.trigger_timestamp,
            mound_distance_cm=request.mound_distance_cm,
            strike_zone=request.strike_zone
        ))

        if result is None:
            return None

        return TrajCalculateResponse(
            isStrike=result.is_strike,
            distanceFromCenter=result.distance_from_center,
            positionOnHomePlate=result.position_on_home_plate,
            curveFunction=result.curve_function,
            getYFunction=result.get_y_function,
            getXFromTimeFunction=result.get_x_from_time_function,
            fullCurveImg=self.image_storage.save_image(result.full_curve_img),
            releaseHeight=result.release_height,
            flightDurationOfMillis=result.flight_duration_of_millis,
            releaseTimestamp=result.release_timestamp,
            curveMinTimestamp=result.curve_min_timestamp,
            curveMaxTimestamp=result.curve_max_timestamp,
            releaseExtension=result.release_extension,
        )
