import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models.base import Base
from src.app.services.pricing import PriceCalculator
from src.app.services.validator import VehicleValidator
from src.app.services.parking_manager import ParkingManager


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def parking_prices():
    return {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}


@pytest.fixture
def price_calculator(parking_prices):
    return PriceCalculator(parking_prices)


@pytest.fixture
def basic_letters():
    return ["B", "C", "D", "E", "F", "G", "K", "L", "N", "O", "P", "R", "S", "T", "W", "Z"]


@pytest.fixture
def special_letters():
    return ["H", "U"]


@pytest.fixture
def vehicle_validator(basic_letters, special_letters):
    return VehicleValidator(basic_letters, special_letters)


@pytest.fixture
def parking_manager(db_session, price_calculator, vehicle_validator):
    return ParkingManager(db_session, price_calculator, vehicle_validator)