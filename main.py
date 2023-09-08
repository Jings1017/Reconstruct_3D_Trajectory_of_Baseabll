import asyncio
import pathlib

from injector import Injector
from tornado.web import Application
from trendup_config.yaml_config import YamlConfig

from src.di.base import BaseModule
from src.di.storage import StorageModuleLocal
from src.di.web import WebModule
from src.web.traj_calculate_controller import TrajCalculateController
from src.web.traj_request_handler import TrajRequestHandler

config = YamlConfig("./settings/config.yml")

container: Injector = Injector([
    BaseModule(config),
    StorageModuleLocal(pathlib.Path(config.get_or_default("storage.path", "./out/storage"))),
    WebModule()
])


async def main():
    app = make_app()
    port = config.get_or_default("web.port", 8082)
    app.listen(port)
    print("Server started on port " + str(port))
    await asyncio.Event().wait()


def make_app():
    return Application(
        [
            (r"/trajectory", TrajRequestHandler, {"controller": container.get(TrajCalculateController)}),
        ]
    )


if __name__ == '__main__':
    asyncio.run(main())
