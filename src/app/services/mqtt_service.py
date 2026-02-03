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
        print("Connected to MQTT Broker")
        self.client.subscribe("parking/entrance/camera")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"MQTT Received: {payload}")

            db = SessionLocal()
            try:
                prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
                manager = ParkingManager(db, PriceCalculator(prices), VehicleValidator(["G", "P", "D"], ["H"]))

                manager.register_entry(
                    payload['country'],
                    payload['registration_no'],
                    payload['floor']
                )
                print(f"Successfully registered via MQTT: {payload['registration_no']}")
            finally:
                db.close()
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()