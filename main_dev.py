import datetime
import json
import os
import pathlib
import tempfile

import attrs
from injector import Injector
from trendup_config.yaml_config import YamlConfig
from trendup_storage.file import StorageFileBasic
from trendup_storage.file_storage import FileStorage
from trendup_storage.models import StorageReference
from trendup_video.web_recorded_video import WebRecordedVideo

from src.di.base import BaseModule
from src.di.storage import StorageModuleLocal
from src.di.web import WebModule
from src.objects import StrikeZoneRequest
from src.web.models import TrajCalculateRequest
from src.web.traj_calculate_controller import TrajCalculateController

config = YamlConfig("./settings/config.yml")

temp_dir = tempfile.TemporaryDirectory()

container: Injector = Injector([
    WebModule(),
    BaseModule(config),
    StorageModuleLocal(storage_path=pathlib.Path(temp_dir.name))
])

total_time: int = 0


def main():
    try:
        run_sample(pathlib.Path("./sample/0901_test1"), pathlib.Path("./out/0901_test1x"))
        # run_sample(pathlib.Path("./sample/wu"), pathlib.Path("./out/wu"))
        # run_all_in_folder(pathlib.Path("./sample"), pathlib.Path("./out"))
    finally:
        temp_dir.cleanup()


def run_all_in_folder(folder: pathlib.Path, out_folder: pathlib.Path):
    for subfolder in folder.iterdir():
        if subfolder.is_dir():
            print(f"Running {subfolder.name}")
            run_sample(subfolder, out_folder / subfolder.name)


def run_sample(folder: pathlib.Path, out_folder: pathlib.Path):
    start_time = datetime.datetime.now()

    controller = container.get(TrajCalculateController)
    js_data = json.load(open(folder / "data.json"))

    videos = [WebRecordedVideo(
        recorder_name=video_js["recorder"],
        storage_reference=save_video_to_storage(folder / (video_js["recorder"] + ".mp4")),
        timestamps=video_js["timestamps"]
    ) for video_js in js_data["videos"]]

    result = controller.calculate(TrajCalculateRequest(
        videos=videos,
        trigger_timestamp=int(js_data["timestamp"]),
        mound_distance_cm=1844,
        strike_zone=StrikeZoneRequest(
            low_cm=60,
            high_cm=140,
        ),
    ))

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    print(result)

    if result is not None:
        img = result.fullCurveImg
        file = container.get(FileStorage).load(img)

        with open(out_folder / "fullCurveImg.png", "wb") as f:
            f.write(file.read())

        json.dump(attrs.asdict(result), open(out_folder / "result.json", "w"), indent=4)

    end_time = datetime.datetime.now()
    print(f"Tooks: {end_time - start_time}")


def save_video_to_storage(path: str) -> StorageReference:
    storage = container.get(FileStorage)
    file = open(path, "rb")
    reference = storage.save(StorageFileBasic("video", "mp4", file.read()))
    return reference


if __name__ == '__main__':
    main()
