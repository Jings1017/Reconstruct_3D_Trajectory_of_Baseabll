from abc import abstractmethod
from typing import Optional

from src.web.models import TrajCalculateResponse, TrajCalculateRequest


class TrajCalculateController:

    @abstractmethod
    def calculate(self, request: TrajCalculateRequest) -> Optional[TrajCalculateResponse]:
        pass
