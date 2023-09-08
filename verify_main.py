from injector import Injector
from trendup_config.yaml_config import YamlConfig

from my_utils import verify
from src.di.base import BaseModule
from src.impl.traj_calculator_impl import TrajCalculatorOptions

config = YamlConfig('./settings/config.yml')

if __name__ == '__main__':
    container: Injector = Injector([
        BaseModule(config),
    ])
    v = verify.VerfiyResult(container.get(TrajCalculatorOptions)).main()
