from typing import List, Tuple, Optional

from attr import define, Factory, attr

from src.web.models import TrajCalculateRequest, TrajCalculateResponse
from src.web.traj_calculate_controller import TrajCalculateController


@define
class TrajCalculateControllerMock(TrajCalculateController):
    _res_map: List[Tuple[TrajCalculateRequest, TrajCalculateResponse]] = attr(default=Factory(list))

    def calculate(self, request: TrajCalculateRequest) -> Optional[TrajCalculateResponse]:
        for req, res in self._res_map:
            if req == request:
                return res

        raise Exception("No mock response found")

    def add_mock_response(self, request: TrajCalculateRequest, response: Optional[TrajCalculateResponse]):
        self._res_map.append((request, response))
