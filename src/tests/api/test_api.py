import requests

BASE_URL = "http://127.0.0.1:8000"


def test_register_vehicle_entry_success():
    payload = {
        "country": "PL",
        "registration_no": "GD5P227",
        "floor": 0
    }

    response = requests.post(f"{BASE_URL}/entry", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] is True
    assert data["registration_no"] == "GD5P227"


def test_register_vehicle_entry_invalid_data():
    payload = {
        "country": "PL",
        "registration_no": "GD1",
        "floor": 0
    }

    response = requests.post(f"{BASE_URL}/entry", json=payload)

    assert response.status_code == 422