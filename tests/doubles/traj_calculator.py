from typing import List, Tuple, Optional

from attr import define, attr, Factory

from src.objects import TrajCalculateMaterials, TrajCalculateResult
from src.traj_calculator import TrajCalculator


@define
class TrajCalculatorMock(TrajCalculator):
    _res_map: List[Tuple[TrajCalculateMaterials, Optional[TrajCalculateResult]]] = attr(default=Factory(list))

    def calculate(self, materials: TrajCalculateMaterials) -> TrajCalculateResult:
        for (m, r) in self._res_map:
            if m == materials:
                return r

        raise Exception("No mock response found")

    def add_mock_response(self, materials: TrajCalculateMaterials, result: Optional[TrajCalculateResult]):
        self._res_map.append((materials, result))
