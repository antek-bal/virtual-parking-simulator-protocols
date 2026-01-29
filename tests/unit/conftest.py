import pytest
from app.services.pricing import PriceCalculator

@pytest.fixture
def parking_prices():
    return {0: 3, 1: 5, 2: 5, 3: 6, 4: 7}

@pytest.fixture
def price_calculator(parking_prices):
    return PriceCalculator(parking_prices)