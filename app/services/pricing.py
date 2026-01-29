from typing import Dict, Union


class PriceCalculator:
    def __init__(self, prices: Dict[str, int | float]):
        self.prices = prices

    def calculate_fee(self, minutes: int, floor: int) -> float:
        if not isinstance(minutes, int):
            raise TypeError("Minutes must be an integer")

        if minutes < 0:
            raise ValueError("Time can't be negative")

        if floor not in self.prices:
            raise ValueError(f"Floor {floor} not in price list")

        if minutes <= 30:
            return 0.0

        fee = ((minutes - 30) / 60) * self.prices[floor]
        return round(fee, 2)
