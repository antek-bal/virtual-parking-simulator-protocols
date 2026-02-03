import paho.mqtt.client as mqtt
import json
from src.app.database import SessionLocal
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully to MQTT Broker")
            self.client.subscribe("parking/entrance/camera")
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            reg_no = payload.get('registration_no')
            country = payload.get('country')
            requested_floor = payload.get('floor')

            print(f"MQTT incoming: {reg_no} ({country})")

            db = SessionLocal()
            try:
                prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
                manager = ParkingManager(
                    db,
                    PriceCalculator(prices),
                    VehicleValidator(["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"],
                                     ["H", "U"])
                )

                result = manager.register_entry(country, reg_no, requested_floor)

                actual_floor = result["floor"]
                actual_spot = result["spot"]

                print(f"SUCCESS: {reg_no} parked on Floor {actual_floor}, Spot {actual_spot}")

                response = {
                    "registration_no": reg_no,
                    "assigned_floor": actual_floor,
                    "assigned_spot": actual_spot,
                    "status": "ALLOWED"
                }
                self.client.publish("parking/entrance/display", json.dumps(response))

            except ValueError as ve:
                print(f"Parking denied for {reg_no}: {ve}")
                error_response = {"registration_no": reg_no, "status": "DENIED", "reason": str(ve)}
                self.client.publish("parking/entrance/display", json.dumps(error_response))
            finally:
                db.close()

        except Exception as e:
            print(f"Critical error in MQTT service: {e}")

    def start(self):
        try:
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Could not connect to MQTT Broker: {e}")