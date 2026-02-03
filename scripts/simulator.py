import time
import random
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "parking/entrance/camera"

client = mqtt.Client()
client.connect("localhost", 1883, 60)


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
            prefix = f"G{random.choice(["A", "BY", "CH", "CZ", "DA", "KA", "KS", "KW", "KY", "KZ", "LE", "MB", "ND", 
                                        "PU", "S", "SL", "SP", "ST", "SZ", "TC", "WE", "WO"])}"
        else:
            first_letter = random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "R", "S", "T", "V", "W", "X", "Y", "Z"])
            second_letter = random.choice(letters)
            prefix = f"{first_letter}{second_letter}"
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
        print("Simulator is running")
    except Exception as e:
        print(f"Error while connecting to broker: {e}")
        return

    while True:
        if random.random() < 0.10:
            vehicle = generate_random_vehicle()
            payload = json.dumps(vehicle)

            client.publish(MQTT_TOPIC, payload)
            print(f"SENT: {vehicle['country']} | {vehicle['registration_no']} has entered the floor {vehicle['floor']}")

        time.sleep(5)


if __name__ == "__main__":
    run_simulation()