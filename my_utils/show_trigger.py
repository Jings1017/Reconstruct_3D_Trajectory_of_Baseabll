import json
import os

import cv2
from trendup_config.yaml_config import YamlConfig

from src.impl.detect_with_API import DetectApi
from src.impl.reconstruct_3d import Reconstruct3D
from src.impl.traj_calculator_impl import TrajCalculatorOptions
from src.objects import TrajPosition, TrajCalculateResult, TrajCalculateMaterials, ReferenceObject
from src.objects import ReferenceObject


class ShowTrigger:

    def __init__(self, options: TrajCalculatorOptions):
        self.options = options


    def main(self):

        out_folder = './out/trigger'
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        left_img = cv2.imread(self.options.left_image_path)
        right_img = cv2.imread(self.options.right_image_path)
        left_out_path = os.path.join(out_folder, 'left_result.png')
        right_out_path = os.path.join(out_folder, 'right_result.png')
       

        data = {
            'left_image': left_out_path,
            'right_image': right_out_path,
        }
        file_path = os.path.join(out_folder, 'data.json')
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)
