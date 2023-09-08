from injector import Module, provider, singleton
from trendup_storage.image.image_storage import ImageStorage
from trendup_video.web.pre_handle_video import PreHandleVideo

from src.traj_calculator import TrajCalculator
from src.web.traj_calculate_controller import TrajCalculateController
from src.web.traj_calculate_controller_impl import TrajCalculateControllerImpl


class WebModule(Module):

    @provider
    @singleton
    def controller(
            self,
            pre_handle_video: PreHandleVideo,
            traj_calculator: TrajCalculator,
            image_storage: ImageStorage
    ) -> TrajCalculateController:
        return TrajCalculateControllerImpl(
            pre_handle_video,
            traj_calculator,
            image_storage,
        )
