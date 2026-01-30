from fastapi import FastAPI, HTTPException
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator

prices = {0:6, 1:5, 2:4, 3:3, 4:2}
calculator = PriceCalculator(prices)
validator = VehicleValidator([["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"], ["H", "U"]])
manager = ParkingManager(calculator, validator)
app = FastAPI(title="Virtual Parking Simulator")

@app.get("/")
def read_root():
    return {"message": "Parking Simulator is online"}

@app.post("/entry")
def register_vehicle_entry(country: str, registration_no: str, floor: int):
    try:
        success = manager.register_entry(country, registration_no, floor)
        return {"status": success, "registration_no": registration_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))