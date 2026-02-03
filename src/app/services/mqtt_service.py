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
        self.is_locked = False

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker")
        self.client.subscribe("parking/entrance/camera")
        self.client.subscribe("parking/exit/camera")
        self.client.subscribe("parking/system/command")
        self.client.subscribe("parking/parking_meter/pay")

    def on_message(self, client, userdata, msg):
        db = SessionLocal()
        try:
            prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
            manager = ParkingManager(db, PriceCalculator(prices), VehicleValidator(["B", "G", "P", "D", "W"], ["H"]))
            payload = json.loads(msg.payload.decode())

            if msg.topic == "parking/system/command":
                if payload.get("cmd") == "LOCK":
                    self.is_locked = True
                    print("SYSTEM LOCKED VIA MQTT")
                elif payload.get("cmd") == "UNLOCK":
                    self.is_locked = False
                    print("SYSTEM UNLOCKED VIA MQTT")

            elif msg.topic == "parking/entrance/camera":
                if self.is_locked:
                    self.client.publish("parking/entrance/display", "SYSTEM LOCKED - WAIT")
                    return

                res = manager.register_entry(payload['country'], payload['registration_no'], payload['floor'])

                sensor_topic = f"parking/sensors/floor/{res['floor']}/spot/{res['spot']}/status"
                self.client.publish(sensor_topic, "OCCUPIED")

                self.client.publish("parking/entrance/display", json.dumps({
                    "msg": "WELCOME", "floor": res['floor'], "spot": res['spot']
                }))

            elif msg.topic == "parking/exit/camera":
                res = manager.register_exit(payload['country'], payload['registration_no'])

                sensor_topic = f"parking/sensors/floor/{res['floor']}/spot/{res['spot']}/status"
                self.client.publish(sensor_topic, "FREE")

                self.client.publish("parking/exit/display", "GOODBYE")

            elif msg.topic == "parking/parking_meter/pay":
                country = payload.get('country')
                reg_no = payload.get('registration_no')

                info = manager.get_payment_info(country, reg_no)
                fee = info['fee']

                self.client.publish(f"parking/parking_meter/display/{reg_no}", f"FEE: {fee} PLN. PROCESSING...")

                manager.pay_parking_fee(country, reg_no, fee)

                payment_status = {
                    "registration_no": reg_no,
                    "amount_paid": fee,
                    "status": "PAID_SUCCESSFULLY",
                    "msg": "TRANSACTION COMPLETE. YOU HAVE 15 MIN TO EXIT."
                }
                self.client.publish(f"parking/parking_meter/status/{reg_no}", json.dumps(payment_status))
                print(f"Payment processed via MQTT for {reg_no}: {fee} PLN")

        except Exception as e:
            print(f"MQTT Error: {e}")
        finally:
            db.close()

    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()