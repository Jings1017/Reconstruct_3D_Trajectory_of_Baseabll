from attr import define
from injector import Module, provider, singleton
from trendup_config.yaml_config import YamlConfig
from trendup_storage.file_storage import FileStorage
from trendup_storage.image.image_storage import ImageStorage
from trendup_storage.image.image_storage_impl import ImageStorageImpl
from trendup_utils.temp_file import TempFile
from trendup_utils.temp_file_impl import TempFileImpl
from trendup_video.download.download_video import DownloadVideo
from trendup_video.download.download_video_impl import DownloadVideoImpl
from trendup_video.reader.video_reader import VideoReader
from trendup_video.reader.video_reader_cv import VideoReaderCV
from trendup_video.web.pre_handle_video import PreHandleVideo
from trendup_video.web.pre_handle_video_impl import PreHandleVideoImpl

from src.impl.detect_with_API import DetectApi
from src.impl.traj_calculator_impl import TrajCalculatorImpl, TrajCalculatorOptions
from src.objects import ReferenceObject
from src.traj_calculator import TrajCalculator


@define
class BaseModule(Module):
    config: YamlConfig

    @provider
    @singleton
    def traj_calculator(self, options: TrajCalculatorOptions) -> TrajCalculator:
        return TrajCalculatorImpl(options)

    @provider
    @singleton
    def calculator_options(self) -> TrajCalculatorOptions:
        cfg = self.config
        return TrajCalculatorOptions(
            skipping_seconds=0.05,
            camera_view_num=cfg.get_or_default('view_num', 4),
            num_of_3d_target_threshold=cfg.get_or_default('num_of_3D_target_threshold', 3),
            skip_interval_pitcher=cfg.get_or_default('skipping_interval.pitcher', 3),
            skip_interval_zone=cfg.get_or_default('skipping_interval.zone', 12),

            conf_threshold=cfg.get_or_default('yolov7_weight.conf_threshold', 0.1),
            detector_pitcher=DetectApi(
                weights=cfg.get_or_default('yolov7_weight.pitcher.path', "YOUR_PATH.pt"),
                conf_thres=cfg.get_or_default('yolov7_weight.pitcher.threshold', 0.1),
                device=cfg.get_or_default('yolo_device', 'cpu')
            ),
            detector_zone=DetectApi(
                weights=cfg.get_or_default('yolov7_weight.zone.path', "YOUR_PATH.pt"),
                conf_thres=cfg.get_or_default('yolov7_weight.zone.threshold', 0.1),
                device=cfg.get_or_default('yolo_device', 'cpu')
            ),

            ref_points_view=[
                cfg.get_or_default('ref_points_view.pitcher.left', "YOUR_PATH.npy"),
                cfg.get_or_default('ref_points_view.pitcher.right', "YOUR_PATH.npy"),
                cfg.get_or_default('ref_points_view.zone.left', "YOUR_PATH.npy"),
                cfg.get_or_default('ref_points_view.zone.right', "YOUR_PATH.npy")
            ],

            mask_view=[
                cfg.get_or_default('mask_view.pitcher.left', "YOUR_PATH.npy"),
                cfg.get_or_default('mask_view.pitcher.right', "YOUR_PATH.npy"),
                cfg.get_or_default('mask_view.zone.left', "YOUR_PATH.npy"),
                cfg.get_or_default('mask_view.zone.right', "YOUR_PATH.npy"),
            ],

            calibration=[
                cfg.get_or_default('calibration.pitcher.left', "YOUR_PATH.npy"),
                cfg.get_or_default('calibration.pitcher.right', "YOUR_PATH.npy"),
                cfg.get_or_default('calibration.zone.left', "YOUR_PATH.npy"),
                cfg.get_or_default('calibration.zone.right', "YOUR_PATH.npy"),
            ],

            box_pitcher=ReferenceObject(
                length=cfg.get_or_default('box_pitcher.length', 46),
                width=cfg.get_or_default('box_pitcher.width', 35),
                height=cfg.get_or_default('box_pitcher.height', 28),
                distance_x=cfg.get_or_default('box_pitcher.distance_x', -35),
                altitude=cfg.get_or_default('box_pitcher.altitude', 27)
            ),

            box_zone=ReferenceObject(
                length=cfg.get_or_default('box_zone.length', 46),
                width=cfg.get_or_default('box_zone.width', 35),
                height=cfg.get_or_default('box_zone.height', 28),
                distance_x=cfg.get_or_default('box_zone.distance_x', 1504.3),
                altitude=cfg.get_or_default('box_zone.altitude', 0)
            ),
            camera_face_box=cfg.get_or_default('camera_face_box', 'backward'),
            img_save_dir=cfg.get_or_default('img_save_dir', './out/images'),
            interval_of_pitch_zone=cfg.get_or_default('interval_of_pitch_zone', 50),
            left_image_path = cfg.get_or_default('verify.left_image_path', 'YOUR_PATH.png'),
            right_image_path = cfg.get_or_default('verify.right_image_path', 'YOUR_PATH.png'),
            verify_mode = cfg.get_or_default('verify.mode', 'pitcher'),
        )

    @provider
    @singleton
    def download_video(self, temp_file: TempFile, file_storage: FileStorage) -> DownloadVideo:
        return DownloadVideoImpl(temp_file, file_storage)

    @provider
    @singleton
    def pre_handle_video(self, download_video: DownloadVideo, video_reader: VideoReader) -> PreHandleVideo:
        return PreHandleVideoImpl(download_video, video_reader)

    @provider
    @singleton
    def image_storage(self, file_storage: FileStorage) -> ImageStorage:
        return ImageStorageImpl(file_storage)

    @provider
    @singleton
    def video_reader(self) -> VideoReader:
        return VideoReaderCV()

    @provider
    @singleton
    def temp_file(self) -> TempFile:
        return TempFileImpl()
