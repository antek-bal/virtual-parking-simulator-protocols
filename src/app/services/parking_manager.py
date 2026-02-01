from typing import List, Optional
from sqlalchemy.orm import Session
from src.app.models.parking import Vehicle, ActiveParking, ParkingHistory
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator
from datetime import datetime, timedelta

class ParkingManager:
    def __init__(self, db: Session, price_calculator: PriceCalculator, validator: VehicleValidator):
        self.db = db
        self.price_calculator = price_calculator
        self.validator = validator

    def register_entry(self, country: str, registration_no: str, floor: int) -> bool:
        if not self.validator.validate(country, registration_no):
            raise ValueError("Invalid registration number")

        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle:
            vehicle = Vehicle(country=country, registration_no=registration_no)
            self.db.add(vehicle)
            self.db.flush()

        if self.db.query(ActiveParking).filter_by(vehicle_id=vehicle.id).first():
            raise ValueError("Vehicle already in the parking")

        new_entry = ActiveParking(vehicle_id=vehicle.id, floor=floor, entry_time=datetime.now())
        self.db.add(new_entry)
        self.db.commit()
        return True

    def get_payment_info(self, country: str, registration_no: str):
        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle or not vehicle.active_parking:
            raise ValueError("Vehicle not found on parking")

        duration = datetime.now() - vehicle.active_parking.entry_time
        minutes = int(duration.total_seconds() / 60)
        fee = self.price_calculator.calculate_fee(minutes, vehicle.active_parking.floor)

        return {"country": country, "registration_no": registration_no, "fee": fee, "minutes": minutes}

    def register_exit(self, country: str, registration_no: str) -> bool:
        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle or not vehicle.active_parking:
            raise ValueError("Vehicle not found on parking")

        active = vehicle.active_parking
        if not active.is_paid:
            raise ValueError("Parking fee not paid")

        if datetime.now() - active.payment_time > timedelta(minutes=15):
            raise ValueError("Payment expired. 15 minutes exceeded")

        history_entry = ParkingHistory(
            vehicle_id=vehicle.id,
            entry_time=active.entry_time,
            exit_time=datetime.now(),
            floor=active.floor,
            fee=active.paid_fee
        )
        self.db.add(history_entry)
        self.db.delete(active)
        self.db.commit()
        return True