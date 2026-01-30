from typing import Dict, Any
from datetime import datetime
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator


class ParkingManager:
    active_parkings: Dict[str, Dict[str, Any]]

    def __init__(self, price_calculator: PriceCalculator, validator: VehicleValidator):
        self.price_calculator = price_calculator
        self.validator = validator
        self.active_parkings = {}

    def register_entry(self, country: str, registration_no: str, floor: int) -> bool:
        if not self.validator.validate(country, registration_no):
            raise ValueError("Invalid registration number")

        if floor not in self.price_calculator.prices:
            raise ValueError(f"Floor {floor} is not available in this parking")

        self.active_parkings[registration_no] = {
            "entry_time": datetime.now(),
            "floor": floor
        }
        return True

    def get_payment_info(self, registration_no: str) -> Dict[str, Any]:
        if registration_no not in self.active_parkings:
            raise ValueError("Vehicle not found on parking")

        entry_data = self.active_parkings[registration_no]

        duration = datetime.now() - entry_data["entry_time"]
        minutes = int(duration.total_seconds() / 60)

        fee = self.price_calculator.calculate_fee(minutes, entry_data["floor"])

        return {"registration_no": registration_no, "fee": fee, "minutes": minutes}

    def register_exit(self, registration_no: str) -> bool:
        if registration_no not in self.active_parkings:
            raise ValueError("Vehicle not found on parking")

        del self.active_parkings[registration_no]
        return True
