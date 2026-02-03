from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional
import os
from contextlib import asynccontextmanager
from src.app.database import engine, get_db
from src.app import models
from src.app.schemas import EntryRequest, UpdateFloorRequest, PaymentRequest
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator
from src.app.services.mqtt_service import MQTTService
from src.app.websocket_manager import ws_manager

mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    mqtt_service.start()
    yield


app = FastAPI(title="Virtual Parking Simulator", lifespan=lifespan)

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


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
    return {"message": "Parking Simulator is online. Go to /dashboard"}


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    base_path = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_path, "templates", "dashboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


security = HTTPBasic()


@app.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == "admin" and credentials.password == "admin":
        return {"status": "Logged in", "token": "demo-token-123"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout():
    return {"status": "Logged out"}


@app.post("/entry", status_code=201)
async def register_vehicle_entry(entry: EntryRequest, manager: ParkingManager = Depends(get_parking_manager)):
    try:
        result = manager.register_entry(entry.country, entry.registration_no, entry.floor)

        await ws_manager.broadcast({
            "type": "VEHICLE_ENTRY",
            "reg_no": entry.registration_no,
            "floor": result['floor'],
            "spot": result['spot']
        })

        return {"status": result, "country": entry.country, "registration_no": entry.registration_no}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/entry/{country}/{registration_no}")
async def update_floor(country: str, registration_no: str, update_data: UpdateFloorRequest,
                 manager: ParkingManager = Depends(get_parking_manager)):
    try:
        manager.change_vehicle_floor(country, registration_no, update_data.new_floor)

        await ws_manager.broadcast({
            "type": "VEHICLE_UPDATED",
            "reg_no": registration_no,
            "floor": update_data.new_floor,
            "msg": f"Moved to Floor {update_data.new_floor}"
        })

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
async def register_vehicle_exit(country: str, registration_no: str,
                                manager: ParkingManager = Depends(get_parking_manager)):
    try:
        result = manager.register_exit(country, registration_no)

        await ws_manager.broadcast({
            "type": "VEHICLE_EXIT",
            "reg_no": registration_no,
            "floor": result['floor'],
            "spot": result['spot']
        })

        return {"status": result, "country": country, "registration_no": registration_no}
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
async def make_payment(country: str, registration_no: str, payment: PaymentRequest,
                       manager: ParkingManager = Depends(get_parking_manager)):
    try:
        manager.pay_parking_fee(country, registration_no, payment.amount)

        await ws_manager.broadcast({
            "type": "PAYMENT_SUCCESS",
            "reg_no": registration_no,
            "amount": payment.amount
        })

        return {"status": "paid", "amount": payment.amount}
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