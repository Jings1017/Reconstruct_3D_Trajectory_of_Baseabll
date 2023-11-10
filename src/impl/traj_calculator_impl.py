import multiprocessing
import time

import cv2
import numpy as np
from attrs import define
from torch.multiprocessing import Queue
from trendup_video.recorded_video import RecordedVideo

from src.impl.detect_with_API import DetectApi
from src.impl.fitting_curve import FindFittingCurve
from src.impl.reconstruct_3d import Reconstruct3D
from src.objects import TrajPosition, TrajCalculateResult, TrajCalculateMaterials, ReferenceObject
from src.traj_calculator import TrajCalculator


@define
class TrajCalculatorOptions:
    skipping_seconds: float

    camera_view_num: int
    num_of_3d_target_threshold: int
    skip_interval_pitcher: int
    skip_interval_zone: int

    conf_threshold: float
    detector_pitcher: DetectApi
    detector_zone: DetectApi

    ref_points_view: list[str]
    mask_view: list[str]
    calibration: list[str]

    box_pitcher: ReferenceObject
    box_zone: ReferenceObject
    camera_face_box: str

    img_save_dir: str
    interval_of_pitch_zone: int

# @define
# class VerifyOptions:
    left_image_path: str
    right_image_path: str
    verify_mode: str


@define
class TrajCalculatorImpl(TrajCalculator):
    options: TrajCalculatorOptions

    def calculate(self, materials: TrajCalculateMaterials) -> TrajCalculateResult:
        process = TrajCalculationProcess(self.options)
        return process.calculate(materials)


class TrajCalculationProcess:
    def __init__(self, options: TrajCalculatorOptions):
        self.options = options

        self.mp_manager = multiprocessing.Manager()
        self.find_fitting_curve = FindFittingCurve(self.options.img_save_dir)
        self.reconstruct3d = Reconstruct3D(self.options.box_pitcher, self.options.box_zone,
                                           self.options.camera_face_box)
        self.exist_front_ball = True
        self.exist_back_ball = True

        self.traj_left_pitcher_video: RecordedVideo = None
        self.traj_right_pitcher_video: RecordedVideo = None
        self.traj_left_zone_video: RecordedVideo = None
        self.traj_right_zone_video: RecordedVideo = None

        self.pitcher_min_video_length = 0
        self.zone_min_video_length = 0

        self.traj_positions = []
        self.traj_positions1 = []
        self.traj_positions2 = []
        self.target1 = np.zeros((1, 4))
        self.target2 = np.zeros((1, 4))

        self.release_time = 0
        self.release_frame_index = 0

        self.target_view = [[] for _ in range(self.options.camera_view_num)]
        self.frame_queue_list = [self.mp_manager.Queue() for _ in range(self.options.camera_view_num)]

    def load_video_data(self, materials: TrajCalculateMaterials):
        self.traj_left_pitcher_video = materials.find_video('TRAJ-LEFT-PITCHER')
        self.traj_right_pitcher_video = materials.find_video('TRAJ-RIGHT-PITCHER')
        self.traj_left_zone_video = materials.find_video('TRAJ-LEFT-ZONE')
        self.traj_right_zone_video = materials.find_video('TRAJ-RIGHT-ZONE')

    def get_release_time_and_frame_index(self, materials: TrajCalculateMaterials):
        # release time = trigger time - 0.2 s
        start_timestamp = self.traj_left_pitcher_video.timestamps[0]
        self.release_time = max(materials.trigger_timestamp - 300, start_timestamp)

        for i in range(len(self.traj_left_pitcher_video.timestamps)):
            if self.release_time < self.traj_left_pitcher_video.timestamps[i]:
                self.release_frame_index = i - 1
                break
        # print('release frame index : ', self.release_frame_index)
        # print('release frame index content : ', self.traj_left_pitcher_video_timestamp[self.release_frame_index])

    def find_trigger_image(self, materials: TrajCalculateMaterials):
        trigger_timestamp = materials.trigger_timestamp

        pitch_left_index = 0
        print('trigger timestamp : ', trigger_timestamp)
        for i in range(len(self.traj_left_pitcher_video.timestamps)):
            if trigger_timestamp < self.traj_left_pitcher_video.timestamps[i]:
                pitch_left_index = i
                break
        pitch_left_img = self.traj_left_pitcher_video.frames[pitch_left_index]
        
        pitch_right_index = 0
        for i in range(len(self.traj_right_pitcher_video.timestamps)):
            if trigger_timestamp < self.traj_right_pitcher_video.timestamps[i]:
                pitch_right_index = i
                break
        pitch_right_img = self.traj_right_pitcher_video.frames[pitch_right_index]
        print('trigger index : ', pitch_left_index, pitch_right_index)
        cv2.imwrite('./out/trigger/trigger_pitcher_left.png', pitch_left_img)
        cv2.imwrite('./out/trigger/trigger_pitcher_right.png', pitch_right_img)

        zone_left_index = 0
        print('trigger timestamp : ', trigger_timestamp)
        for i in range(len(self.traj_left_zone_video.timestamps)):
            if trigger_timestamp < self.traj_left_zone_video.timestamps[i]:
                zone_left_index = i
                break
        zone_left_img = self.traj_left_zone_video.frames[zone_left_index]
        
        zone_right_index = 0
        for i in range(len(self.traj_right_zone_video.timestamps)):
            if trigger_timestamp < self.traj_right_zone_video.timestamps[i]:
                zone_right_index = i
                break
        zone_right_img = self.traj_right_zone_video.frames[zone_right_index]
        print('trigger index : ', zone_left_index, zone_right_index)
        cv2.imwrite('./out/trigger/trigger_zone_left.png', zone_left_img)
        cv2.imwrite('./out/trigger/trigger_zone_right.png', zone_right_img)
        

    def yolo_inference(self, img_queue: Queue, ball_of_all_frames: list, detector: DetectApi):
        for _ in range(img_queue.qsize()):
            current_frame = img_queue.get()
            result, names = detector.detect([current_frame])
            current_ball_list = []
            for cls, (x1, y1, x2, y2), conf in result[0][1]:
                middle_x = (x1 + x2) // 2
                middle_y = (y1 + y2) // 2
                middle_point = (middle_x, middle_y)
                current_ball_list.append([conf, middle_point])
            ball_of_all_frames.append(current_ball_list)

    def delete_data(self, i: int, data_x: np.array, data_y: np.array, data_z: np.array, data_frame_idx: np.array):
        data_z = np.delete(data_z, i)
        data_y = np.delete(data_y, i)
        data_x = np.delete(data_x, i)
        data_frame_idx = np.delete(data_frame_idx, i)

    def calculate(self, materials: TrajCalculateMaterials) -> TrajCalculateResult:

        self.load_video_data(materials)
        self.get_release_time_and_frame_index(materials)
        # self.find_trigger_image(materials)
        total_start_time = time.time()

        print('release frmae index ', self.release_frame_index)

        if self.options.camera_view_num == 4:
            # -------------- frame extractor --------------
            print(f'------- FRAME EXTRACTING -------')
            self.pitcher_min_video_length = min(len(self.traj_left_pitcher_video.timestamps), len(self.traj_right_pitcher_video.timestamps))
            for idx in range(self.pitcher_min_video_length):
                img = self.traj_left_pitcher_video.frames[idx]
                try:
                    img2 = self.traj_right_pitcher_video.frames[idx]
                except:
                    break
                if img is None or img2 is None:
                    break
                if idx < max(self.release_frame_index-50, 0) or idx >= min(self.release_frame_index+100, self.pitcher_min_video_length):
                    continue
                elif idx % self.options.skip_interval_pitcher == 0:
                    self.frame_queue_list[0].put(img)
                    self.frame_queue_list[1].put(img2)

            print(f'PITCH : {self.frame_queue_list[0].qsize()} and {self.frame_queue_list[1].qsize()}')

            self.zone_min_video_length = min(len(self.traj_left_zone_video.timestamps), len(self.traj_right_zone_video.timestamps))
            for idx in range(self.zone_min_video_length):
                img3 = self.traj_left_zone_video.frames[idx]
                try:
                    img4 = self.traj_right_zone_video.frames[idx]
                except:
                    break
                if img3 is None or img4 is None:
                    break
                if idx < min(self.release_frame_index + 80, self.zone_min_video_length) or idx > min(self.release_frame_index + 400, self.zone_min_video_length):
                    continue
                if idx % self.options.skip_interval_zone == 0:
                    self.frame_queue_list[2].put(img3)
                    self.frame_queue_list[3].put(img4)

            print(f'ZONE : {self.frame_queue_list[2].qsize()} and {self.frame_queue_list[3].qsize()}')

            # -------------- detecting --------------
            print(f'------- YOLO INFERENCE -------')
            st_time = time.time()
            self.yolo_inference(self.frame_queue_list[0], self.target_view[0], self.options.detector_pitcher)
            self.yolo_inference(self.frame_queue_list[1], self.target_view[1], self.options.detector_pitcher)
            elapsed_time = int(time.time() - st_time)
            print(f'pitcher inference time : {elapsed_time:.2f} s')

            st_time = time.time()
            self.yolo_inference(self.frame_queue_list[2], self.target_view[2], self.options.detector_zone)
            self.yolo_inference(self.frame_queue_list[3], self.target_view[3], self.options.detector_zone)
            elapsed_time = int(time.time() - st_time)
            print(f'pitcher inference time : {elapsed_time:.2f} s')

            # -------------- reconstruct 3D trajectory and return the raw data --------------

            target, target_view1_for_display, target_view2_for_display, court = self.reconstruct3d.reconstruction(
                self.target_view[0],
                self.target_view[1],
                self.options.ref_points_view[0],
                self.options.ref_points_view[1],
                self.options.mask_view[0],
                self.options.mask_view[1],
                self.options.calibration[0],
                self.options.calibration[1],
                'pitcher',
                False,
            )

            target2, target_view3_for_display, target_view4_for_display, court = self.reconstruct3d.reconstruction(
                self.target_view[2],
                self.target_view[3],
                self.options.ref_points_view[2],
                self.options.ref_points_view[3],
                self.options.mask_view[2],
                self.options.mask_view[3],
                self.options.calibration[2],
                self.options.calibration[3],
                'zone',
                False,
            )
            
            print(f'------- 3D TARGETS -------')

            origin_target_count = 0
            if target is not None:
                origin_target_count = target[0].shape[0]
                self.target1 = np.resize(self.target1, (origin_target_count, 4))
                self.target1 = target
            print(f'Reconstruct {origin_target_count} targets in PITCH')

            origin_target2_count = 0
            if target2 is not None:
                origin_target2_count = target2[0].shape[0]
                self.target2 = np.resize(self.target2, (origin_target2_count, 4))
                self.target2 = target2
            print(f'Reconstruct {origin_target2_count} targets in ZONE')

            # --------------------- postprocessing --------------------------

            # Both is None -> return None
            if target is None and target2 is None:
                print('Can Not Reconstruct Any Point !')
                return None

            if target is not None:
                data_x = self.target1[1]
                data_y = self.target1[0]
                data_z = self.target1[2]
                data_frame_idx = self.target1[3]

                # compute the real timestamp index
                for i in range(self.target1[3].shape[0]):
                    data_frame_idx[i] = target[3][i] * self.options.skip_interval_pitcher

                data_frame_idx += self.release_frame_index

                # delete first error ball
                # data_min_x = np.min(data_x)
                # print('data min x ', data_min_x)
                # data_min_index = 0
                # for i in range(data_x.shape[0]):
                #     if data_x[i] == data_min_x:
                #         break
                #     else:
                #         data_min_index += 1
                # print('data min index : ', data_min_index)
                # for i in reversed(range(data_x.shape[0])):
                #     if i < data_min_index:
                #         print('delete ', i)
                #         data_x = np.delete(data_x, i)
                #         data_y = np.delete(data_y, i)
                #         data_z = np.delete(data_z, i)
                #         data_frame_idx = np.delete(data_frame_idx, i)

                for i in range(data_x.shape[0]):
                    tp1 = TrajPosition(x=data_x[i], y=data_y[i], z=data_z[i],
                                       timestamp=self.traj_left_pitcher_video.timestamps[int(data_frame_idx[i])])
                    self.traj_positions1.append(tp1)

            if target2 is not None:
                data2_x = target2[1]
                data2_y = target2[0]
                data2_z = target2[2]
                data2_frame_idx = target2[3]

                # compute the real timestamp index
                for i in range(target2[3].shape[0]):
                    data2_frame_idx[i] = target2[3][i] * self.options.skip_interval_zone
                data2_frame_idx += self.release_frame_index + self.options.interval_of_pitch_zone

                # delete first error ball
                # data2_min_x = np.min(data2_x)
                # print('data2 min x ', data2_min_x)
                # data2_min_index = 0
                # for i in range(data2_x.shape[0]):
                #     if data2_x[i] == data2_min_x:
                #         break
                #     else:
                #         data2_min_index += 1
                # print('data2 min index : ', data2_min_index)
                # for i in reversed(range(data2_x.shape[0])):
                #     if i < data2_min_index:
                #         data2_x = np.delete(data2_x, i)
                #         data2_y = np.delete(data2_y, i)
                #         data2_z = np.delete(data2_z, i)
                #         data2_frame_idx = np.delete(data2_frame_idx, i)

                for i in range(data2_x.shape[0]):
                    tp1 = TrajPosition(x=data2_x[i], y=data2_y[i], z=data2_z[i],
                                       timestamp=self.traj_left_zone_video.timestamps[int(data2_frame_idx[i])])
                    self.traj_positions2.append(tp1)

            # print('-------------- traj_pos  --------------')
            if len(self.traj_positions1) <= 2 :
                self.exist_front_ball = False
                self.traj_positions = self.traj_positions2
            elif len(self.traj_positions2) <= 2 :
                self.exist_back_ball = False
                self.traj_positions = self.traj_positions1
            else:
                self.traj_positions = self.traj_positions1 + self.traj_positions2

            # if reconstructing nothing or bad result -> use the default result
            if len(self.traj_positions) < self.options.num_of_3d_target_threshold:
                print('# of Points is less than threshold ')
                return None


        elif self.options.camera_view_num == 2:
            print(f'------- FRAME EXTRACTING -------')
            self.pitcher_min_video_length = min(len(self.traj_left_pitcher_video.timestamps), len(self.traj_right_pitcher_video.timestamps))
            for idx in range(self.pitcher_min_video_length):
                img = self.traj_left_pitcher_video.frames[idx]
                try:
                    img2 = self.traj_right_pitcher_video.frames[idx]
                except:
                    break
                if img is None or img2 is None:
                    break
                if idx < max(self.release_frame_index, 0) or idx >= min(self.release_frame_index+400, self.pitcher_min_video_length):
                    continue
                elif idx % self.options.skip_interval_pitcher == 0:
                    self.frame_queue_list[0].put(img)
                    self.frame_queue_list[1].put(img2)

            print(f'PITCH : {self.frame_queue_list[0].qsize()} and {self.frame_queue_list[1].qsize()}')

            # -------------- detecting --------------
            print(f'------- YOLO INFERENCE -------')
            st_time = time.time()
            self.yolo_inference(self.frame_queue_list[0], self.target_view[0], self.options.detector_pitcher)
            self.yolo_inference(self.frame_queue_list[1], self.target_view[1], self.options.detector_pitcher)
            elapsed_time = int(time.time() - st_time)
            print(f'pitcher inference time : {elapsed_time:.2f} s')

            # -------------- reconstruct 3D trajectory and return the raw data --------------

            target, target_view1_for_display, target_view2_for_display, court = self.reconstruct3d.reconstruction(
                self.target_view[0],
                self.target_view[1],
                self.options.ref_points_view[0],
                self.options.ref_points_view[1],
                self.options.mask_view[0],
                self.options.mask_view[1],
                self.options.calibration[0],
                self.options.calibration[1],
                'pitcher',
                False,
            )

            print(f'------- 3D TARGETS -------')
            print(f'Reconstruct {target[0].shape[0]} targets in PITCH')


            # --------------------- postprocessing --------------------------

            if target is not None:
                data_x = target[1]
                data_y = target[0]
                data_z = target[2]
                data_frame_idx = target[3]

                # compute the real timestamp index
                for i in range(target[3].shape[0]):
                    data_frame_idx[i] = target[3][i] * self.options.skip_interval_pitcher
                data_frame_idx += self.release_frame_index

                # print('-------------- traj_pos 1 --------------')
                for i in range(data_x.shape[0]):
                    tp1 = TrajPosition(x=data_x[i], y=data_y[i], z=data_z[i],
                                       timestamp=self.traj_left_pitcher_video.timestamps[int(data_frame_idx[i])])
                    self.traj_positions1.append(tp1)

            else:
                print('Can Not Reconstruct Any Point !')
                # default_data = np.load('./src/impl/target_data/default_3d_targets.npz')
                return None

            self.traj_positions = self.traj_positions1[1:]

        # -------------- fitting curve with 3d points ---------------

        traj_result = self.find_fitting_curve.get_fitting_curve_data(self.traj_positions, self.release_time, materials,
                                                                     self.exist_front_ball, self.exist_back_ball)

        print(f'------- TIME COST -------')
        print(f'time cost : {(time.time() - total_start_time):.2f} s')
        print(f'-------------------------')
        return traj_result
