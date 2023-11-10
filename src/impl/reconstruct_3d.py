import cv2
import matplotlib
import numpy as np
import sys

matplotlib.use("TkAgg")
from typing import Tuple
from src.objects import ReferenceObject


class Reconstruct3D:
    def __init__(self, box_pitcher: ReferenceObject, box_zone: ReferenceObject, camera_face_box: str):

        self.box_pitcher = box_pitcher
        self.box_zone = box_zone

        self.camera_face_box = camera_face_box

        self.proj_map1 = np.zeros((3, 4))
        self.proj_map2 = np.zeros((3, 4))

        self.target_view1_for_display = []
        self.target_view2_for_display = []

        self.last_ball_view1 = []
        self.last_ball_view2 = []

        self.view1_outliers = []
        self.view2_outliers = []

        self.single_target_view_1 = []
        self.single_target_view_2 = []

        self.view1_idx = -1
        self.view2_idx = -1

        self.target_3d_points = np.zeros((10, 4))

    def cal_distance(self, current_ball: [int, int], last_ball: [int, int]) -> float:
        diff_x = current_ball[0] - last_ball[0]
        diff_y = current_ball[1] - last_ball[1]
        return (diff_x ** 2 + diff_y ** 2) ** 0.5

    def remove_outliers(self, view1: list, view2: list, mask_view1: str, mask_view2: str):

        mask1 = cv2.imread(mask_view1)
        mask2 = cv2.imread(mask_view2)

        new_view1, new_view2 = [], []

        for i in range(len(view1)):
            value = view1[i]
            x = value[1][0]
            y = value[1][1]
            if mask1[y][x][0] != 0:
                new_view1.append(value)
        for i in range(len(view2)):
            value = view2[i]
            x = value[1][0]
            y = value[1][1]
            if mask2[y][x][0] != 0:
                new_view2.append(value)

        return new_view1, new_view2

    def get_moving_ball(self, balls: list, outliers: list, last_ball_position: list) -> (int, list):
        if len(outliers) == 0:
            outliers = balls
            if len(outliers) == 0:
                return -1, outliers
            return 0, outliers

        new_ball_distance = [sys.maxsize] * (len(balls))
        for i in reversed(range(len(balls))):
            is_new_ball = True
            for j in range(len(outliers)):
                if (
                        abs(balls[i][1][0] - outliers[j][1][0]) <= 1
                        and abs(balls[i][1][1] - outliers[j][1][1]) <= 1
                ):
                    is_new_ball = False
                    break
            if is_new_ball:
                outliers.append(balls[i])
                if last_ball_position == []:
                    return i, outliers
                new_ball_distance[i] = self.cal_distance(balls[i][1], last_ball_position[1])

        negative_count = 0
        for k in range(len(new_ball_distance)):
            if new_ball_distance[k] == sys.maxsize:
                negative_count += 1
        if negative_count < len(new_ball_distance):
            moving_ball_index = new_ball_distance.index(min(new_ball_distance))
            return moving_ball_index, outliers
        return -1, outliers

    def get_projection_maps(self, mode: str, ref_points_view1: list, ref_points_view2: list, calib_left: str,
                            calib_right: str):
        if mode == 'pitcher':
            self.proj_map1, self.proj_map2 = self.project_points(
                src_points_1=self.get_ref_points(ref_points_view1),
                src_points_2=self.get_ref_points(ref_points_view2),
                dst_points=self.get_ref_points(),
                dist_1=np.load(calib_left)["dist_coefs"],
                mtx_1=np.load(calib_left)["camera_matrix"],
                dist_2=np.load(calib_right)["dist_coefs"],
                mtx_2=np.load(calib_right)["camera_matrix"],
            )
        elif mode == 'zone':
            self.proj_map1, self.proj_map2 = self.project_points(
                src_points_1=self.get_ref_points(ref_points_view1),
                src_points_2=self.get_ref_points(ref_points_view2),
                dst_points=self.get_ref_points(ref_points='zone_dst_points'),
                dist_1=np.load(calib_left)["dist_coefs"],
                mtx_1=np.load(calib_left)["camera_matrix"],
                dist_2=np.load(calib_right)["dist_coefs"],
                mtx_2=np.load(calib_right)["camera_matrix"],
            )

    def get_3d_targets_frame_by_frame(self, frames, mode: str, mask_view1: str, mask_view2: str, ref_points_view1: list,
                                      ref_points_view2: list, verify:bool):
        target_frame_num = []
        if not verify:
            for frame_num, frame in enumerate(frames):
                view1, view2 = frame
                view1, view2 = self.remove_outliers(view1, view2, mask_view1, mask_view2)

                self.view1_idx, self.view1_outliers = self.get_moving_ball(view1, self.view1_outliers, self.last_ball_view1)
                self.view2_idx, self.view2_outliers = self.get_moving_ball(view2, self.view2_outliers, self.last_ball_view2)

                if self.view1_idx != -1 and self.view2_idx != -1:
                    self.last_ball_view1 = view1[self.view1_idx]
                    self.last_ball_view2 = view2[self.view2_idx]

                self.target_view1_for_display.append(view1[self.view1_idx] if self.view1_idx != -1 else None)
                self.target_view2_for_display.append(view2[self.view2_idx] if self.view2_idx != -1 else None)

                if self.view1_idx != -1 and self.view2_idx != -1:
                    self.single_target_view_1 = np.array(
                        [[view1[self.view1_idx][1][0], view1[self.view1_idx][1][1]]],
                        dtype="int",
                    )
                    self.single_target_view_2 = np.array(
                        [[view2[self.view2_idx][1][0], view2[self.view2_idx][1][1]]],
                        dtype="int",
                    )
                    if mode == 'pitcher':
                        court, target = self.generate_3d_target(
                            target_view1=self.single_target_view_1,
                            target_view2=self.single_target_view_2,
                            src_points_1=self.get_ref_points(ref_points_view1),
                            src_points_2=self.get_ref_points(ref_points_view2),
                        )
                    elif mode == 'zone':
                        court, target = self.generate_3d_target(
                            target_view1=self.single_target_view_1,
                            target_view2=self.single_target_view_2,
                            src_points_1=self.get_ref_points(ref_points_view1),
                            src_points_2=self.get_ref_points(ref_points_view2),
                        )
                    target.append(frame_num)
                    target_frame_num.append(target)
        else:
            for frame_num, frame in enumerate(frames):
                view1, view2 = frame
                self.view1_idx = 0
                self.view2_idx = 0
                self.single_target_view_1 = np.array(
                    [[view1[1][0], view1[1][1]]],
                    dtype="int",
                )
                self.single_target_view_2 = np.array(
                    [[view2[1][0], view2[1][1]]],
                    dtype="int",
                )
                if mode == 'pitcher':
                    court, target = self.generate_3d_target(
                        target_view1=self.single_target_view_1,
                        target_view2=self.single_target_view_2,
                        src_points_1=self.get_ref_points(ref_points_view1),
                        src_points_2=self.get_ref_points(ref_points_view2),
                    )
                elif mode == 'zone':
                    court, target = self.generate_3d_target(
                        target_view1=self.single_target_view_1,
                        target_view2=self.single_target_view_2,
                        src_points_1=self.get_ref_points(ref_points_view1),
                        src_points_2=self.get_ref_points(ref_points_view2),
                    )
                target.append(frame_num)
                target_frame_num.append(target)

        target_frame_num = np.array(target_frame_num)
        target = target_frame_num.T
        self.target_3d_points = np.resize(self.target_3d_points, target.shape)
        self.target_3d_points = target

    def reset_3d_origin(self, mode: str):
        if mode == 'pitcher' and self.target_3d_points is not None:
            for i in range(self.target_3d_points[1].shape[0]):
                self.target_3d_points[1][i] = self.target_3d_points[1][i] + self.box_pitcher.distance_x
                self.target_3d_points[0][i] = self.target_3d_points[0][i] - self.box_pitcher.length / 2
                self.target_3d_points[2][i] = self.target_3d_points[2][i] - self.box_pitcher.altitude
        elif mode == 'zone' and self.target_3d_points is not None:
            for i in range(self.target_3d_points[1].shape[0]):
                self.target_3d_points[1][i] = self.target_3d_points[1][i] + self.box_zone.distance_x
                self.target_3d_points[0][i] = self.target_3d_points[0][i] - self.box_zone.length / 2
                self.target_3d_points[2][i] = self.target_3d_points[2][i] - self.box_zone.altitude

    def generate_3d_target(self, target_view1: np.array, target_view2: np.array, src_points_1: list,
                           src_points_2: list) -> Tuple[np.array, np.array]:
        points_view1 = np.array(src_points_1).astype("float32")
        points_view2 = np.array(src_points_2).astype("float32")

        points1 = np.concatenate((points_view1, target_view1), axis=0)
        points2 = np.concatenate((points_view2, target_view2), axis=0)

        points_3D = cv2.triangulatePoints(self.proj_map1, self.proj_map2, points1.T, points2.T)

        points_3D = points_3D / points_3D[3]
        x, y, z, w = points_3D

        target = [x[-1], y[-1], z[-1]]
        court = [x[:-1], y[:-1], z[:-1]]
        return court, target

    def project_points(
            self,
            src_points_1: list,
            src_points_2: list,
            dst_points: list,
            dist_1: np.array,
            mtx_1: np.array,
            dist_2: np.array,
            mtx_2: np.array,
    ) -> Tuple[np.array, np.array]:
        points_view1 = np.array([src_points_1]).astype("float32")
        points_view2 = np.array([src_points_2]).astype("float32")
        dst_points_pnp = np.array([dst_points]).astype("float32")

        retval1, rvec1, tvec1 = cv2.solvePnP(dst_points_pnp, points_view1, mtx_1, dist_1)
        r1, _ = cv2.Rodrigues(rvec1)
        retval2, rvec2, tvec2 = cv2.solvePnP(dst_points_pnp, points_view2, mtx_2, dist_2)
        r2, _ = cv2.Rodrigues(rvec2)

        proj_map_1 = np.matmul(mtx_1, np.concatenate((r1, tvec1), axis=1))
        proj_map_2 = np.matmul(mtx_2, np.concatenate((r2, tvec2), axis=1))

        return proj_map_1, proj_map_2

    def get_ref_points(self, ref_points="pitcher_dst_points"):

        if ref_points == "pitcher_dst_points":
            if self.camera_face_box == 'backward':
                return [
                    [self.box_pitcher.length, self.box_pitcher.width, 0],
                    [self.box_pitcher.length, self.box_pitcher.width, self.box_pitcher.height],
                    [self.box_pitcher.length, 0, self.box_pitcher.height],
                    [0, self.box_pitcher.width, 0],
                    [0, self.box_pitcher.width, self.box_pitcher.height],
                    [0, 0, self.box_pitcher.height],
                ]
            return [
                [0, 0, 0],
                [0, 0, self.box_pitcher.height],
                [0, self.box_pitcher.width, self.box_pitcher.height],
                [self.box_pitcher.length, 0, 0],
                [self.box_pitcher.length, 0, self.box_pitcher.height],
                [self.box_pitcher.length, self.box_pitcher.width, self.box_pitcher.height],
            ]
        elif ref_points == "zone_dst_points":
            return [
                [0, 0, 0],
                [0, 0, self.box_zone.height],
                [0, self.box_zone.width, self.box_zone.height],
                [self.box_zone.length, 0, 0],
                [self.box_zone.length, 0, self.box_zone.height],
                [self.box_zone.length, self.box_zone.width, self.box_zone.height],
            ]
        else:
            return np.load(ref_points, allow_pickle=True)

    def reconstruction(
            self,
            target_view1: list,
            target_view2: list,
            ref_points_view1: list,
            ref_points_view2: list,
            mask_view1: str,
            mask_view2: str,
            calib_left: str,
            calib_right: str,
            mode: str,
            verify: bool
    ):

        court = None
        frames = zip(target_view1, target_view2)

        self.get_projection_maps(mode, ref_points_view1, ref_points_view2, calib_left, calib_right)

        self.get_3d_targets_frame_by_frame(frames, mode, mask_view1, mask_view2, ref_points_view1, ref_points_view2, verify)

        court = np.array(self.get_ref_points()).T

        # If there is no ball, just add court points.
        if self.target_3d_points.shape[-1] == 0:
            self.target_3d_points = None

        self.reset_3d_origin(mode)

        court_x, court_y, court_z = court[0], court[1], court[2]
        for i in range(court_x.shape[0]):
            court_y[i] += self.box_zone.distance_x
            court_x[i] -= self.box_zone.length / 2

        court = np.array(court).T

        return self.target_3d_points, self.target_view1_for_display, self.target_view2_for_display, court
