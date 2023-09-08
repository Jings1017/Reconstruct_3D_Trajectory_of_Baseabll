import numpy as np
from trendup_video.recorded_video import RecordedVideo
from trendup_video.type_alias import Frame
from trendup_video.video_data import VideoInfo

from src.objects import TrajPosition, CurveFunctionParameters, GetYFunctionParameters, GetXFromTimeFunctionParameters, \
    TrajCalculateResult


class Stubs:
    @staticmethod
    def traj_position() -> TrajPosition:
        return TrajPosition(
            x=1.0,
            y=2.0,
            z=3.0,
            timestamp=4
        )

    @staticmethod
    def curve_fun_params() -> CurveFunctionParameters:
        return CurveFunctionParameters(
            a=1.0,
            b=2.0,
            c=3.0,
            d=4.0,
            e=5.0,
        )

    @staticmethod
    def get_y_fun_params() -> GetYFunctionParameters:
        return GetYFunctionParameters(
            a=1.0,
            b=2.0,
            c=3.0,
        )

    @staticmethod
    def get_x_from_time_fun_params() -> GetXFromTimeFunctionParameters:
        return GetXFromTimeFunctionParameters(
            a=1.0,
            b=2.0,
        )

    @staticmethod
    def recorded_video(frames=2) -> RecordedVideo:
        info = Stubs.video_info()
        info.frames = [Stubs.frame(i) for i in range(frames)]
        return RecordedVideo(
            info=info,
            recorder_name="LEFT",
            timestamps=[frame for frame in range(frames)]
        )

    @staticmethod
    def video_info() -> VideoInfo:
        return VideoInfo(
            frames=[Stubs.frame(), Stubs.frame(), Stubs.frame()],
            width=800,
            height=600,
            fps=300
        )

    @staticmethod
    def frame(value=0) -> Frame:
        return np.array([[value, value, value], [value, value, value]])

    @staticmethod
    def traj_calculate_result() -> TrajCalculateResult:
        return TrajCalculateResult(
            is_strike=True,
            is_land_early=False,
            distance_from_center=1.0,
            position_on_home_plate=Stubs.traj_position(),
            curve_function=Stubs.curve_fun_params(),
            get_y_function=Stubs.get_y_fun_params(),
            get_x_from_time_function=Stubs.get_x_from_time_fun_params(),
            full_curve_img="base64",
            release_height=1.0,
            flight_duration_of_millis=2,
            release_timestamp=3,
            curve_min_timestamp=4,
            curve_max_timestamp=5,
        )
