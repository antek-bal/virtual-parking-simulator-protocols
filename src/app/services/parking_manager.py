from typing import List, Dict, Any
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

    def register_entry(self, country: str, registration_no: str, requested_floor: int) -> Dict[str, Any]:
        if not self.validator.validate(country, registration_no):
            raise ValueError("Invalid registration number")

        if requested_floor < 0 or requested_floor > 4:
            raise ValueError(f"Floor {requested_floor} is not available")

        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle:
            vehicle = Vehicle(country=country, registration_no=registration_no)
            self.db.add(vehicle)
            self.db.flush()

        if self.db.query(ActiveParking).filter_by(vehicle_id=vehicle.id).first():
            raise ValueError("Vehicle already in the parking")

        all_floors = [0, 1, 2, 3, 4]
        search_order = [requested_floor] + [f for f in all_floors if f != requested_floor]

        assigned_floor = None
        assigned_spot = None

        for floor in search_order:
            occupied = self.db.query(ActiveParking.spot_number).filter_by(floor=floor).all()
            occupied_spots = {s[0] for s in occupied}

            for spot in range(1, 51):
                if spot not in occupied_spots:
                    assigned_floor = floor
                    assigned_spot = spot
                    break

            if assigned_spot:
                break

        if assigned_spot is None:
            raise ValueError("Parking is completely full")

        new_entry = ActiveParking(vehicle_id=vehicle.id, floor=assigned_floor, spot_number=assigned_spot, entry_time=datetime.now())
        self.db.add(new_entry)
        self.db.commit()
        return {
            "floor": assigned_floor,
            "spot": assigned_spot,
            "status": True,
        }

    def get_payment_info(self, country: str, registration_no: str) -> Dict[str, Any]:
        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle or not vehicle.active_parking:
            raise ValueError("Vehicle not found on parking")

        duration = datetime.now() - vehicle.active_parking.entry_time
        minutes = int(duration.total_seconds() / 60)
        fee = self.price_calculator.calculate_fee(minutes, vehicle.active_parking.floor)

        return {
            "country": country,
            "registration_no": registration_no,
            "fee": fee,
            "minutes": minutes
        }

    def pay_parking_fee(self, country: str, registration_no: str, amount: float) -> Dict[str, Any]:
        payment_info = self.get_payment_info(country, registration_no)
        required_fee = payment_info["fee"]

        if amount < required_fee:
            raise ValueError("Insufficient amount")

        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        active = vehicle.active_parking

        active.is_paid = True
        active.payment_time = datetime.now()
        active.paid_fee = required_fee

        self.db.commit()

        return {
            "status": True,
            "fee": required_fee,
            "payment_time": active.payment_time
        }

    def register_exit(self, country: str, registration_no: str) -> Dict[str, Any]:
        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle or not vehicle.active_parking:
            raise ValueError("Vehicle not found on parking")

        active = vehicle.active_parking
        if not active.is_paid:
            raise ValueError("Parking fee not paid")

        if datetime.now() - active.payment_time > timedelta(minutes=15):
            raise ValueError("Payment expired. 15 minutes exceeded")

        floor = active.floor
        spot = active.spot_number

        history_entry = ParkingHistory(
            vehicle_id=vehicle.id,
            entry_time=active.entry_time,
            exit_time=datetime.now(),
            floor=floor,
            fee=active.paid_fee
        )
        self.db.add(history_entry)
        self.db.delete(active)
        self.db.commit()
        return {"floor": floor, "spot" : spot, "status": True}

    def change_vehicle_floor(self, country: str, registration_no: str, new_floor: int) -> Dict[str, Any]:
        if new_floor < 0 or new_floor > 4:
            raise ValueError(f"Floor {new_floor} is not available")

        vehicle = self.db.query(Vehicle).filter_by(registration_no=registration_no, country=country).first()
        if not vehicle or not vehicle.active_parking:
            raise ValueError("Vehicle not found on parking")

        occupied = self.db.query(ActiveParking.spot_number).filter_by(floor=new_floor).all()
        occupied_spots = {s[0] for s in occupied}

        assigned_spot = None
        for spot in range(1, 51):
            if spot not in occupied_spots:
                assigned_spot = spot
                break

        if assigned_spot is None:
            raise ValueError(f"No free spots on floor {new_floor}")

        vehicle.active_parking.floor = new_floor
        vehicle.active_parking.spot_number = assigned_spot

        self.db.commit()
        return {"status": True, "new_floor": new_floor, "new_spot": assigned_spot}