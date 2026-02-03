import pytest
import random
import time
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.app import models


PERF_DB_FILE = "perf_stability_test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{PERF_DB_FILE}"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine_test)

from src.app.main import app, get_db
from src.app.models.base import Base

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestPerformance:
    @pytest.fixture(scope="class", autouse=True)
    def setup_db(self):
        Base.metadata.create_all(bind=engine_test)
        yield
        Base.metadata.drop_all(bind=engine_test)
        engine_test.dispose()
        if os.path.exists(PERF_DB_FILE):
            os.remove(PERF_DB_FILE)

    @pytest.fixture
    def client(self):
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)

    def test_parking_entry_performance(self, client):
        for _ in range(1000):
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
            assert (end - start) < 0.5

    def test_mass_payment_and_exit_performance(self, client):
        registrations = []
        for _ in range(100):
            unique_id = str(uuid.uuid4()).upper()[:7]
            reg_no = f"X{unique_id}"
            res = client.post("/entry", json={"country": "PL", "registration_no": reg_no, "floor": 0})
            if res.status_code == 201:
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