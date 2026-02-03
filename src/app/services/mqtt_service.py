import paho.mqtt.client as mqtt
import json
import asyncio
from src.app.database import SessionLocal
from src.app.services.parking_manager import ParkingManager
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator
from src.app.websocket_manager import ws_manager


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.is_locked = False
        self.loop = asyncio.get_event_loop()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker")
        self.client.subscribe("parking/entrance/camera")
        self.client.subscribe("parking/exit/camera")
        self.client.subscribe("parking/system/command")
        self.client.subscribe("parking/parking_meter/pay")

    def send_to_ws(self, data: dict):
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(data), self.loop)

    def on_message(self, client, userdata, msg):
        db = SessionLocal()
        try:
            prices = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}
            p_manager = ParkingManager(db, PriceCalculator(prices), VehicleValidator(["B", "G", "P", "D", "W"], ["H"]))
            payload = json.loads(msg.payload.decode())

            if msg.topic == "parking/system/command":
                cmd = payload.get("cmd")
                if cmd == "LOCK":
                    self.is_locked = True
                elif cmd == "UNLOCK":
                    self.is_locked = False

                self.send_to_ws({
                    "type": "EMERGENCY_STATUS",
                    "is_locked": self.is_locked,
                    "msg": f"Parking is now {'LOCKED' if self.is_locked else 'OPEN'}"
                })

            elif msg.topic == "parking/entrance/camera":
                if self.is_locked:
                    self.client.publish("parking/entrance/display", "SYSTEM LOCKED")
                    return

                res = p_manager.register_entry(payload['country'], payload['registration_no'], payload['floor'])

                sensor_topic = f"parking/sensors/floor/{res['floor']}/spot/{res['spot']}/status"
                self.client.publish(sensor_topic, "OCCUPIED")

                self.send_to_ws({
                    "type": "VEHICLE_ENTRY",
                    "reg_no": payload['registration_no'],
                    "floor": res['floor'],
                    "spot": res['spot'],
                    "time": "Just now"
                })

            elif msg.topic == "parking/exit/camera":
                res = p_manager.register_exit(payload['country'], payload['registration_no'])

                sensor_topic = f"parking/sensors/floor/{res['floor']}/spot/{res['spot']}/status"
                self.client.publish(sensor_topic, "FREE")

                self.send_to_ws({
                    "type": "VEHICLE_EXIT",
                    "reg_no": payload['registration_no'],
                    "floor": res['floor'],
                    "spot": res['spot']
                })

            elif msg.topic == "parking/parking_meter/pay":
                country = payload.get('country')
                reg_no = payload.get('registration_no')
                info = p_manager.get_payment_info(country, reg_no)
                fee = info['fee']

                p_manager.pay_parking_fee(country, reg_no, fee)

                self.send_to_ws({
                    "type": "PAYMENT_SUCCESS",
                    "reg_no": reg_no,
                    "amount": fee,
                    "total_on_parking": "updated"
                })

        except Exception as e:
            print(f"MQTT Error: {e}")
        finally:
            db.close()

    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()