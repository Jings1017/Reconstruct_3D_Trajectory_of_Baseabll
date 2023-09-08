from abc import abstractmethod

from src.objects import TrajCalculateResult, TrajCalculateMaterials


class TrajCalculator:

    @abstractmethod
    def calculate(self, materials: TrajCalculateMaterials) -> TrajCalculateResult:
        pass
