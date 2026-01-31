import pytest, random, time, uuid
from fastapi.testclient import TestClient
from src.app.main import app


class TestPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_parking_entry_performance(self, client):
        for i in range(1000):
            unique_id = str(uuid.uuid4()).upper()[:7]
            reg_no = f"G{unique_id}"
            payload = {
                "country": "PL",
                "registration_no": reg_no,
                "floor": random.randint(0, 4)
            }

            start = time.perf_counter()
            response = client.post("/entry", json=payload)
            end = time.perf_counter()

            assert response.status_code == 201

            duration = end - start
            assert duration < 0.5

    def test_mass_payment_and_exit_performance(self, client):
        registrations = []
        for reg in range(1000):
            unique_id = str(uuid.uuid4()).upper()[:7]
            reg_no = f"G{unique_id}"
            client.post("/entry", json={"country": "PL", "registration_no": reg_no, "floor": 0})
            registrations.append(reg_no)

        for reg in registrations:
            start_pay = time.perf_counter()
            pay_resp = client.post(f"/payment/PL/{reg}", json={"amount": 100.0})
            end_pay = time.perf_counter()

            assert pay_resp.status_code == 200
            assert (end_pay - start_pay) < 0.5

            start_exit = time.perf_counter()
            exit_resp = client.delete(f"/entry/PL/{reg}")
            end_exit = time.perf_counter()

            assert exit_resp.status_code == 200
            assert (end_exit - start_exit) < 0.5