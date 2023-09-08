import json
import os

import cv2
from trendup_config.yaml_config import YamlConfig

from src.impl.detect_with_API import DetectApi
from src.impl.reconstruct_3d import Reconstruct3D
from src.impl.traj_calculator_impl import TrajCalculatorOptions
from src.objects import ReferenceObject


class VerfiyResult:

    def __init__(self, options: TrajCalculatorOptions):
        self.options = options

        self.left_detect_ball = []
        self.right_detect_ball = []

        self.reconstruct3d = Reconstruct3D(self.options.box_pitcher, self.options.box_zone,
                                           self.options.camera_face_box)

    def yolo_inference(self, img, detector: DetectApi, save_name: str) -> list:
        result, names = detector.detect([img])
        result_img = result[0][0]
        cv2.imwrite(save_name, result_img)
        current_ball_list = []
        for cls, (x1, y1, x2, y2), conf in result[0][1]:
            middle_x = (x1 + x2) // 2
            middle_y = (y1 + y2) // 2
            middle_point = (middle_x, middle_y)
            current_ball_list.append([conf, middle_point])
        return current_ball_list

    def main(self):

        out_folder = './out/verify'
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
        print(self.options)
        left_img = cv2.imread(self.options.left_image_path)
        right_img = cv2.imread(self.options.right_image_path)
        left_out_path = os.path.join(out_folder, 'left_result.png')
        right_out_path = os.path.join(out_folder, 'right_result.png')
        self.left_detect_ball = self.yolo_inference(left_img, self.options.detector_pitcher, left_out_path)
        self.right_detect_ball = self.yolo_inference(right_img, self.options.detector_pitcher, right_out_path)

        self.left_detect_ball = [max(self.left_detect_ball)]
        self.right_detect_ball = [max(self.right_detect_ball)]

        print(self.left_detect_ball, self.right_detect_ball)

        target, target_view1_for_display, target_view2_for_display, court = self.reconstruct3d.reconstruction(
            self.left_detect_ball,
            self.right_detect_ball,
            self.options.ref_points_view[0],
            self.options.ref_points_view[1],
            self.options.mask_view[0],
            self.options.mask_view[1],
            self.options.calibration[0],
            self.options.calibration[1],
            self.options.verify_mode,
            True,
        )

        verify_x = target[1][0]
        verify_y = target[0][0]
        verify_z = target[2][0]

        print('(x,y,z) = ({:.2f} {:.2f} {:.2f})'.format(verify_x, verify_y, verify_z))

        data = {
            'left_image': left_out_path,
            'right_image': right_out_path,
            'predict_point': {'x': verify_x, 'y': verify_y, 'z': verify_z}
        }
        file_path = os.path.join(out_folder, 'data.json')
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)
