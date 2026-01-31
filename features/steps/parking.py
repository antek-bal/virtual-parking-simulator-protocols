from behave import *
import requests

URL = "http://localhost:8000"


@step('Active parkings is empty')
def clear_active_parkings(context):
    response = requests.get(URL + "/vehicles")
    assert response.status_code == 200
    vehicles = response.json()

    for vehicle_id in vehicles:
        country, reg = vehicle_id.split('_')
        requests.post(URL + f"/payment/{country}/{reg}", json={"amount": 1000.0})
        requests.delete(URL + f"/entry/{country}/{reg}")


@when('Vehicle from "{country}" with registration number "{reg_no}" has entered the parking lot on floor {floor:d}')
def vehicle_enters(context, country, reg_no, floor):
    json_body = {
        "country": country,
        "registration_no": reg_no,
        "floor": floor
    }
    response = requests.post(URL + "/entry", json=json_body)
    assert response.status_code == 201
    context.vehicle_id = f"{country}_{reg_no}"


@then('Number of active parkings equals {count:d}')
def check_active_count(context, count):
    response = requests.get(URL + "/vehicles")
    assert response.status_code == 200
    assert len(response.json()) == count


@step('{minutes:d} minutes have passed since the entry time')
def wait_time(context, minutes):
    context.minutes_passed = minutes


@when('Driver makes a card payment of {amount:f}')
def driver_pays(context, amount):
    country, reg = context.vehicle_id.split('_')
    json_body = {"amount": amount}
    response = requests.post(URL + f"/payment/{country}/{reg}", json=json_body)
    assert response.status_code == 200


@step('Driver attempts to exit {minutes:d} minutes after paying')
def exit_attempt_delay(context, minutes):
    context.exit_delay = minutes


@then('The system should remove the vehicle from the active parkings list')
def check_vehicle_removed(context):
    country, reg = context.vehicle_id.split('_')
    response = requests.delete(URL + f"/entry/{country}/{reg}")

    assert response.status_code == 200
    assert response.json()["status"] is True

    check_resp = requests.get(URL + "/vehicles")
    assert context.vehicle_id not in check_resp.json()


@step('Save the session information in the history')
def check_history(context):
    response = requests.get(URL + "/entry/history")
    assert response.status_code == 200
    history = response.json()

    assert context.vehicle_id in history
    assert len(history[context.vehicle_id]) > 0