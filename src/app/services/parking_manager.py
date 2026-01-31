from collections import defaultdict
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator


class ParkingManager:
    active_parkings: Dict[str, Dict[str, Any]]
    history: Dict[str, List[Dict[str, Any]]]

    def __init__(self, price_calculator: PriceCalculator, validator: VehicleValidator):
        self.price_calculator = price_calculator
        self.validator = validator
        self.active_parkings = {}
        self.history = defaultdict(list)

    def register_entry(self, country: str, registration_no: str, floor: int) -> bool:
        if not self.validator.validate(country, registration_no):
            raise ValueError("Invalid registration number")

        vehicle_id = f"{country}_{registration_no}"

        if vehicle_id in self.active_parkings:
            raise ValueError("Vehicle already in the parking")

        if floor not in self.price_calculator.prices:
            raise ValueError(f"Floor {floor} is not available in this parking")

        self.active_parkings[vehicle_id] = {
            "entry_time": datetime.now(),
            "floor": floor,
            "is_paid": False,
            "payment_time": None,
            "paid_fee": None
        }
        return True

    def get_payment_info(self, country: str, registration_no: str) -> Dict[str, Any]:
        vehicle_id = f"{country}_{registration_no}"
        if vehicle_id not in self.active_parkings:
            raise ValueError("Vehicle not found on parking")

        entry_data = self.active_parkings[vehicle_id]

        duration = datetime.now() - entry_data["entry_time"]
        minutes = int(duration.total_seconds() / 60)

        fee = self.price_calculator.calculate_fee(minutes, entry_data["floor"])

        return {"country": country, "registration_no": registration_no, "fee": fee, "minutes": minutes}

    def pay_parking_fee(self, country: str, registration_no: str, amount: float) -> Dict[str, Any]:
        payment_info = self.get_payment_info(country, registration_no)
        required_fee = payment_info["fee"]

        if amount < required_fee:
            raise ValueError("Insufficient amount")

        vehicle_id = f"{country}_{registration_no}"

        self.active_parkings[vehicle_id]["is_paid"] = True
        self.active_parkings[vehicle_id]["payment_time"] = datetime.now()
        self.active_parkings[vehicle_id]["paid_fee"] = required_fee

        return {
            "status": True,
            "fee": required_fee,
            "payment_time": datetime.now()
        }


    def register_exit(self, country: str, registration_no: str) -> bool:
        vehicle_id = f"{country}_{registration_no}"

        if vehicle_id not in self.active_parkings:
            raise ValueError("Vehicle not found on parking")

        entry_data = self.active_parkings[vehicle_id]

        if not entry_data["is_paid"]:
            raise ValueError("Parking fee not paid")

        time_since_pay = datetime.now() - entry_data["payment_time"]
        if time_since_pay > timedelta(minutes=15):
            raise ValueError("Payment expired. 15 minutes exceeded")

        self.history[vehicle_id].append({
            "entry_time": entry_data["entry_time"],
            "exit_time": datetime.now(),
            "floor": entry_data["floor"],
            "fee": entry_data["paid_fee"]
        })

        del self.active_parkings[vehicle_id]
        return True

    def change_vehicle_floor(self, country: str, registration_no: str, new_floor: int) -> bool:
        vehicle_id = f"{country}_{registration_no}"
        if vehicle_id not in self.active_parkings:
            raise ValueError("Vehicle not found on parking")
        if new_floor not in self.price_calculator.prices:
            raise ValueError(f"Floor {new_floor} is not available in this parking")

        self.active_parkings[vehicle_id]["floor"] = new_floor
        return True
