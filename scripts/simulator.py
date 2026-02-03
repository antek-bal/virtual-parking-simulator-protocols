import time
import random
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_ENTRANCE = "parking/entrance/camera"
TOPIC_EXIT = "parking/exit/camera"
TOPIC_PAYMENT = "parking/parking_meter/pay"

client = mqtt.Client()

parked_vehicles = []


def generate_random_vehicle():
    letters = "ABCDEFGHJKLMNPQRSTUWXYZ"
    n = random.randint(1, 100)
    if n <= 94:
        country = "PL"
    elif n <= 98:
        country = "UA"
    elif n <= 99:
        country = "DE"
    else:
        country = random.choice(["CZ", "SK", "LT"])

    if country == "PL":
        n = random.randint(1, 100)
        if n <= 90:
            prefix = "GD"
        elif n <= 95:
            prefix = f"G{random.choice(['A', 'BY', 'CH', 'CZ', 'DA', 'KA', 'KS', 'KW', 'KY', 'KZ', 'LE', 'MB', 'ND', 'PU', 'S', 'SL', 'SP', 'ST', 'SZ', 'TC', 'WE', 'WO'])}"
        else:
            first_letters = ["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"]
            prefix = f"{random.choice(first_letters)}{random.choice(letters)}"
        reg_no = f"{prefix}{random.choice(letters)}{random.randint(100, 999)}{random.choice(letters)}"
    else:
        reg_no = f"{random.choice(letters)}{random.choice(letters)}{random.randint(100, 999)}{random.choice(letters)}"

    return {
        "country": country,
        "registration_no": reg_no,
        "floor": random.randint(0, 4)
    }


def run_simulation():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"Simulator running")
    except Exception as e:
        print(f"Error while connecting to Broker: {e}")
        return

    while True:
        chance = random.random()

        if chance < 0.15:
            vehicle = generate_random_vehicle()
            client.publish(TOPIC_ENTRANCE, json.dumps(vehicle))
            parked_vehicles.append(vehicle)
            print(f"[ENTRY] Camera: {vehicle['country']}_{vehicle['registration_no']}, Floor: {vehicle['floor']}")

        elif 0.15 <= chance < 0.25:
            if parked_vehicles:
                v = random.choice(parked_vehicles)
                payload = {"country": v['country'], "registration_no": v['registration_no']}
                client.publish(TOPIC_PAYMENT, json.dumps(payload))
                print(f"[PAY] Parking meter: Payment for {v['registration_no']}")

        elif 0.25 <= chance < 0.30:
            if parked_vehicles:
                v = parked_vehicles.pop(0)
                payload = {"country": v['country'], "registration_no": v['registration_no']}
                client.publish(TOPIC_EXIT, json.dumps(payload))
                print(f"[EXIT] Exit camera: {v['registration_no']}")

        time.sleep(3)


if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        client.disconnect()