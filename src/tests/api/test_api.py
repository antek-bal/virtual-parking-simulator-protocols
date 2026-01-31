import requests

BASE_URL = "http://127.0.0.1:8000"


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

    response = requests.get(f"{BASE_URL}/payment/{country}/{reg_no}")
    assert response.status_code == 200
    fee = response.json()["fee"]

    payment_payload = {"amount": fee}
    response = requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json=payment_payload)
    assert response.status_code == 200
    assert response.json()["status"] is True

    update_payload = {"new_floor": 2}
    response = requests.patch(f"{BASE_URL}/entry/{country}/{reg_no}", json=update_payload)
    assert response.status_code == 200

    response = requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")
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
    requests.patch(f"{BASE_URL}/entry/PL/GD5P227", json={"floor": 0})


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

    response = requests.patch(f"{BASE_URL}/entry/{payload['country']}/{payload['registration_no']}",
                              json=payload_updated)

    assert response.status_code == 422


def test_register_vehicle_exit_success():
    payload = {"country": "PL", "registration_no": "GD5P227", "floor": 0}
    requests.post(f"{BASE_URL}/entry", json=payload)

    requests.post(f"{BASE_URL}/payment/PL/GD5P227", json={"amount": 100.0})

    response = requests.delete(f"{BASE_URL}/entry/PL/GD5P227")
    assert response.status_code == 200
    assert response.json()["status"] is True


def test_register_vehicle_exit_fail_not_paid():
    country = "PL"
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": country, "registration_no": reg_no, "floor": 0})

    response = requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")
    assert response.status_code == 400
    assert "not paid" in response.json()["detail"]


def test_register_vehicle_exit_invalid_registration():
    response = requests.delete(f"{BASE_URL}/entry/PL/GD5P227")

    assert response.status_code == 400


def test_payment_success():
    country = "PL"
    reg_no = "GD999XX"

    requests.post(f"{BASE_URL}/entry", json={
        "country": country,
        "registration_no": reg_no,
        "floor": 0
    })

    payment_payload = {"amount": 10.0}
    response = requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json=payment_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] is True
    assert "fee" in data
    assert "payment_time" in data


def test_payment_insufficient_funds():
    country = "PL"
    reg_no = "GD77777"
    requests.post(f"{BASE_URL}/entry", json={"country": country, "registration_no": reg_no, "floor": 0})

    response = requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json={"amount": -1.0})
    assert response.status_code == 400 or response.status_code == 422


def test_get_vehicles_list():
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": "GD5P227", "floor": 1})
    response = requests.get(f"{BASE_URL}/vehicles")
    assert response.status_code == 200
    assert "PL_GD5P227" in response.json()


def test_search_vehicles():
    requests.post(f"{BASE_URL}/entry", json={"country": "PL", "registration_no": "GD5P227", "floor": 0})
    response = requests.get(f"{BASE_URL}/vehicles/search?q=GD")
    assert response.status_code == 200
    assert "PL_GD5P227" in response.json()


def test_get_history():
    country = "PL"
    reg_no = "GD5P227"
    requests.post(f"{BASE_URL}/entry", json={"country": country, "registration_no": reg_no, "floor": 0})

    requests.post(f"{BASE_URL}/payment/{country}/{reg_no}", json={"amount": 50.0})
    requests.delete(f"{BASE_URL}/entry/{country}/{reg_no}")

    response = requests.get(f"{BASE_URL}/entry/history")
    assert response.status_code == 200
    assert f"{country}_{reg_no}" in response.json()
