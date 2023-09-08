from unittest import TestCase

from trendup_storage.image.image_storage_mock import ImageStorageMock
from trendup_storage.models import StorageReference
from trendup_video.web.pre_handle_video_mock import PreHandleVideoMock

from src.objects import TrajCalculateMaterials, StrikeZoneRequest, TrajCalculateResult
from src.web.models import TrajCalculateRequest, TrajCalculateResponse
from src.web.traj_calculate_controller_impl import TrajCalculateControllerImpl
from tests.doubles.traj_calculator import TrajCalculatorMock
from tests.stubs import Stubs
from tests.web_stubs import WebStubs


class TestTrajCalculateControllerImpl(TestCase):

    def setUp(self):
        self.calculator = TrajCalculatorMock()
        self.pre_handle_video = PreHandleVideoMock()
        self.image_storage = ImageStorageMock()

        self.web_video = WebStubs.recorded_video()
        self.recorded_video = Stubs.recorded_video()
        self.storage_reference = StorageReference(
            env="LOCAL",
            id="FILE_ID",
        )

        self.controller = TrajCalculateControllerImpl(
            self.pre_handle_video,
            self.calculator,
            self.image_storage,
        )

    def test_should_return_none_if_calculator_returns_none(self):
        self.pre_handle_video.set_response([self.web_video], [self.recorded_video])
        self.calculator.add_mock_response(
            self._get_sample_materials(),
            None
        )

        self.assertIsNone(self.controller.calculate(self._get_sample_request()))

    def test_should_map_calculate_result_to_response(self):
        self.pre_handle_video.set_response([self.web_video], [self.recorded_video])
        self.calculator.add_mock_response(
            self._get_sample_materials(),
            self._get_sample_result()
        )

        self.image_storage.set_response(Stubs.frame(2), self.storage_reference)

        self.assertEqual(
            self.controller.calculate(self._get_sample_request()),
            self._get_sample_response()
        )

    def _get_sample_request(self) -> TrajCalculateRequest:
        return TrajCalculateRequest(
            videos=[self.web_video],
            trigger_timestamp=123,
            mound_distance_cm=27,
            strike_zone=StrikeZoneRequest(
                low_cm=2,
                high_cm=3
            )
        )

    def _get_sample_materials(self) -> TrajCalculateMaterials:
        return TrajCalculateMaterials(
            videos=[Stubs.recorded_video()],
            trigger_timestamp=123,
            mound_distance_cm=27,
            strike_zone=StrikeZoneRequest(
                low_cm=2,
                high_cm=3
            )
        )

    def _get_sample_result(self) -> TrajCalculateResult:
        return TrajCalculateResult(
            is_strike=True,
            is_land_early=False,
            distance_from_center=1.0,
            position_on_home_plate=Stubs.traj_position(),
            curve_function=Stubs.curve_fun_params(),
            get_y_function=Stubs.get_y_fun_params(),
            get_x_from_time_function=Stubs.get_x_from_time_fun_params(),
            full_curve_img=Stubs.frame(2),
            release_height=1.0,
            flight_duration_of_millis=2,
            release_timestamp=3,
            curve_min_timestamp=4,
            curve_max_timestamp=5,
            release_extension=6,
        )

    def _get_sample_response(self) -> TrajCalculateResponse:
        return TrajCalculateResponse(
            isStrike=True,
            distanceFromCenter=1.0,
            positionOnHomePlate=Stubs.traj_position(),
            curveFunction=Stubs.curve_fun_params(),
            getYFunction=Stubs.get_y_fun_params(),
            getXFromTimeFunction=Stubs.get_x_from_time_fun_params(),
            fullCurveImg=self.storage_reference,
            releaseHeight=1.0,
            flightDurationOfMillis=2,
            releaseTimestamp=3,
            curveMinTimestamp=4,
            curveMaxTimestamp=5,
            releaseExtension=6,
        )
