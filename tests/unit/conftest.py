import pytest
from app.services.pricing import PriceCalculator
from app.services.validator import VehicleValidator

@pytest.fixture
def parking_prices():
    return {0: 3, 1: 5, 2: 5, 3: 6, 4: 7}

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