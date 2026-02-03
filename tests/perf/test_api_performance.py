import pytest
import random
import time
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.app.main import app, get_db
from src.app import models
from src.app.models.base import Base

PERF_DB_FILE = "perf_stability_test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{PERF_DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestPerformance:
    @pytest.fixture(scope="class", autouse=True)
    def setup_db(self):
        if os.path.exists(PERF_DB_FILE):
            try:
                os.remove(PERF_DB_FILE)
            except PermissionError:
                pass

        Base.metadata.create_all(bind=engine)

        yield

        Base.metadata.drop_all(bind=engine)

        engine.dispose()

        if os.path.exists(PERF_DB_FILE):
            try:
                time.sleep(0.5)
                os.remove(PERF_DB_FILE)
            except PermissionError:
                print(f"Ostrzeżenie: Nie udało się usunąć {PERF_DB_FILE}. Plik zostanie nadpisany w kolejnym teście.")

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