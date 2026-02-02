from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from src.app.database import engine, get_db
from src.app import models
from src.app.schemas import EntryRequest, UpdateFloorRequest, PaymentRequest
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Virtual Parking Simulator")


def get_parking_manager(db: Session = Depends(get_db)):
    prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
    calculator = PriceCalculator(prices)
    validator = VehicleValidator(
        ["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"],
        ["H", "U"]
    )
    return ParkingManager(db, calculator, validator)


@app.get("/")
def read_root():
    return {"message": "Parking Simulator is online"}


@app.post("/entry", status_code=201)
def register_vehicle_entry(entry: EntryRequest, manager: ParkingManager = Depends(get_parking_manager)):
    try:
        success = manager.register_entry(entry.country, entry.registration_no, entry.floor)
        return {"status": success, "country": entry.country, "registration_no": entry.registration_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/entry/{country}/{registration_no}")
def update_floor(country: str, registration_no: str, update_data: UpdateFloorRequest,
                 manager: ParkingManager = Depends(get_parking_manager)):
    try:
        manager.change_vehicle_floor(country, registration_no, update_data.new_floor)
        return {
            "status": True,
            "country": country,
            "registration_no": registration_no,
            "new_floor": update_data.new_floor
        }
    except ValueError as e:
        status_code = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@app.delete("/entry/{country}/{registration_no}")
def register_vehicle_exit(country: str, registration_no: str, manager: ParkingManager = Depends(get_parking_manager)):
    try:
        success = manager.register_exit(country, registration_no)
        return {"status": success, "country": country, "registration_no": registration_no}
    except ValueError as e:
        status_code = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get("/payment/{country}/{registration_no}")
def get_payment(country: str, registration_no: str, manager: ParkingManager = Depends(get_parking_manager)):
    try:
        return manager.get_payment_info(country, registration_no)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/payment/{country}/{registration_no}", status_code=200)
def make_payment(country: str, registration_no: str, payment: PaymentRequest,
                 manager: ParkingManager = Depends(get_parking_manager)):
    try:
        return manager.pay_parking_fee(country, registration_no, payment.amount)
    except ValueError as e:
        status_code = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get('/vehicles')
def get_list_of_vehicles(db: Session = Depends(get_db)):
    return db.query(models.ActiveParking).options(joinedload(models.ActiveParking.vehicle)).all()


@app.get('/entry/history')
def get_history(db: Session = Depends(get_db)):
    return db.query(models.ParkingHistory).options(joinedload(models.ParkingHistory.vehicle)).all()


@app.get("/vehicles/search")
def search_vehicles(q: str, db: Session = Depends(get_db)):
    return db.query(models.Vehicle).filter(models.Vehicle.registration_no.ilike(f"%{q}%")).all()
