import requests
import pytest

BASE_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def cleanup():
    yield


def test_root():
    response = requests.get(f"{BASE_URL}/")
    data = response.json()
    assert response.status_code == 200
    assert data["message"] == "Parking Simulator is online"


def test_full_vehicle_lifecycle():
    country = "PL"
    reg_no = "GD5P227"

    entry_payload = {"country": country, "registration_no": reg_no, "floor": 0}
    response = requests.post(f"{BASE_URL}/entry", json=entry_payload)
    assert response.status_code == 201

    # 2. Get Payment Info
    response = requests.get(f"{BASE_URL}/payment/{country}/{reg_no}")
    assert response.status_code == 200
    fee = response.json()["fee"]

    # 3. Pay
    payment_payload = {"amount": fee}
    response = requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json=payment_payload)
    assert response.status_code == 200
    assert response.json()["status"] is True

    # 4. Update Floor
    update_payload = {"new_floor": 2}
    response = requests.patch(f"{BASE_URL}/entry/{country}/{reg_no}", json=update_payload)
    assert response.status_code == 200

    # 5. Exit
    response = requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")
    assert response.status_code == 200
    assert response.json()["status"] is True


def test_register_vehicle_entry_invalid_data():
    payload = {"country": "PL", "registration_no": "GD1", "floor": 0}
    response = requests.post(f"{BASE_URL}/entry", json=payload)
    assert response.status_code == 422


def test_update_floor_invalid_registration():
    response = requests.patch(f"{BASE_URL}/entry/PL/GD5P227", json={"new_floor": 2})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_floor_invalid_floor():
    payload = {"new_floor": 5}
    response = requests.patch(f"{BASE_URL}/entry/PL/GD5P227", json=payload)
    assert response.status_code == 422


def test_register_vehicle_exit_fail_not_paid():
    country = "PL"
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": country, "registration_no": reg_no, "floor": 0})

    response = requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")
    assert response.status_code == 400
    assert "not paid" in response.json()["detail"].lower()


def test_get_vehicles_list():
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": reg_no, "floor": 1})

    response = requests.get(f"{BASE_URL}/vehicles")
    assert response.status_code == 200
    vehicles = response.json()
    assert any(v['vehicle']['registration_no'] == reg_no for v in vehicles)


def test_search_vehicles():
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": reg_no, "floor": 0})

    response = requests.get(f"{BASE_URL}/vehicles/search?q=GD")
    assert response.status_code == 200
    results = response.json()
    assert any(v['registration_no'] == reg_no for v in results)


def test_get_history():
    country = "PL"
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": country, "registration_no": reg_no, "floor": 0})
    requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json={"amount": 100.0})
    requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")

    response = requests.get(f"{BASE_URL}/entry/history")
    assert response.status_code == 200
    history = response.json()
    assert any(h['vehicle']['registration_no'] == reg_no for h in history)