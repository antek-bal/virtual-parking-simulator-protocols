from fastapi import FastAPI, HTTPException
from src.app.schemas import EntryRequest, UpdateFloorRequest
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator

prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
calculator = PriceCalculator(prices)
validator = VehicleValidator(["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"],
                             ["H", "U"])
manager = ParkingManager(calculator, validator)
app = FastAPI(title="Virtual Parking Simulator")


@app.get("/")
def read_root():
    return {"message": "Parking Simulator is online"}


@app.post("/entry", status_code=201)
def register_vehicle_entry(entry: EntryRequest):
    try:
        success = manager.register_entry(entry.country, entry.registration_no, entry.floor)
        return {"status": success, "country": entry.country, "registration_no": entry.registration_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/entry/{country}/{registration_no}")
def update_floor(country: str, registration_no: str, update_data: UpdateFloorRequest):
    vehicle_id = f"{country}_{registration_no}"
    if vehicle_id not in manager.active_parkings:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    try:
        manager.change_vehicle_floor(country, registration_no, update_data.new_floor)
        return {
            "status": True,
            "country": country,
            "registration_no": registration_no,
            "new_floor": update_data.new_floor
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/entry/{country}/{registration_no}")
def register_vehicle_exit(country: str, registration_no: str):
    vehicle_id = f"{country}_{registration_no}"
    if vehicle_id not in manager.active_parkings:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    try:
        success = manager.register_exit(country, registration_no)
        return {"status": success, "country": country, "registration_no": registration_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/payment/{country}/{registration_no}")
def get_payment(country: str, registration_no: str):
    vehicle_id = f"{country}_{registration_no}"
    if vehicle_id not in manager.active_parkings:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    try:
        return manager.get_payment_info(country, registration_no)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/vehicles')
def get_list_of_vehicles():
    return manager.active_parkings


@app.get('/entry/history')
def get_history():
    return manager.history

@app.get("/vehicles/search")
def search_vehicles(q: str):
    return {reg: data for reg, data in manager.active_parkings.items() if q.upper() in reg.upper()}