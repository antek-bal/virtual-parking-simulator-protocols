import requests

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    response = requests.get(f"{BASE_URL}/")
    data = response.json()

    assert response.status_code == 200
    assert data["message"] == "Parking Simulator is online"


def test_full_vehicle_lifecycle():
    reg_no = "GD5P227"

    entry_payload = {
        "country": "PL",
        "registration_no": reg_no,
        "floor": 0
    }
    response = requests.post(f"{BASE_URL}/entry", json=entry_payload)
    assert response.status_code == 201
    assert response.json()["registration_no"] == reg_no

    response = requests.get(f"{BASE_URL}/payment/{reg_no}")
    assert response.status_code == 200
    assert "fee" in response.json()

    update_payload = {"new_floor": 2}
    response = requests.patch(f"{BASE_URL}/entry/{reg_no}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["new_floor"] == 2

    response = requests.delete(f"{BASE_URL}/entry/{reg_no}")
    assert response.status_code == 200
    assert response.json()["status"] is True

def test_register_vehicle_entry_invalid_data():
    payload = {
        "country": "PL",
        "registration_no": "GD1",
        "floor": 0
    }

    response = requests.post(f"{BASE_URL}/entry", json=payload)

    assert response.status_code == 422

def test_update_floor_invalid_registration():
    payload = {
        "registration_no": "GD5P227"
    }

    requests.patch(f"{BASE_URL}/entry/{payload["registration_no"]}", json={"floor": 0})

def test_update_floor_invalid_floor():
    payload = {
        "country": "PL",
        "registration_no": "GD5P227",
        "floor": 0
    }

    requests.post(f"{BASE_URL}/entry", json=payload)

    payload_updated = {
        "new_floor": 5
    }

    response = requests.patch(f"{BASE_URL}/entry/{payload["registration_no"]}", json=payload_updated)

    assert response.status_code == 422

def test_register_vehicle_exit_success():
    payload = {
        "country": "PL",
        "registration_no": "GD5P227",
        "floor": 0
    }
    requests.post(f"{BASE_URL}/entry", json=payload)

    response = requests.delete(f"{BASE_URL}/entry/{payload['registration_no']}")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] is True
    assert data["registration_no"] == payload["registration_no"]

def test_register_vehicle_exit_invalid_registration():
    response = requests.delete(f"{BASE_URL}/entry/GD5P227")

    assert response.status_code == 404


def test_get_vehicles_list():
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": "GD5P227", "floor": 1})
    response = requests.get(f"{BASE_URL}/vehicles")
    assert response.status_code == 200
    assert "GD5P227" in response.json()


def test_search_vehicles():
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": "GD5P227", "floor": 0})
    response = requests.get(f"{BASE_URL}/vehicles/search?q=GD")
    assert response.status_code == 200
    assert "GD5P227" in response.json()


def test_get_history():
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": reg_no, "floor": 0})
    requests.delete(f"{BASE_URL}/entry/{reg_no}")

    response = requests.get(f"{BASE_URL}/entry/history")
    assert response.status_code == 200
    assert reg_no in response.json()
    assert len(response.json()[reg_no]) > 0
