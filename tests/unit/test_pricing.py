import pytest
from app.services.pricing import PriceCalculator


class TestPriceCalculator:
    def test_free_thirty_minutes(self, price_calculator):
        for i in range(5):
            assert price_calculator.calculate_fee(30, i) == 0.0

    def test_over_thirty_minutes(self, price_calculator):
        assert price_calculator.calculate_fee(90, 0) == 3.0
        assert price_calculator.calculate_fee(90, 1) == 5.0
        assert price_calculator.calculate_fee(90, 2) == 5.0
        assert price_calculator.calculate_fee(90, 3) == 6.0
        assert price_calculator.calculate_fee(90, 4) == 7.0

    def test_negative_minutes(self, price_calculator):
        with pytest.raises(ValueError):
            price_calculator.calculate_fee(-30, 0)

    def test_incorrect_floor(self, price_calculator):
        with pytest.raises(ValueError):
            price_calculator.calculate_fee(90, 5)

    def test_minutes_not_int(self, price_calculator):
        with pytest.raises(TypeError):
            price_calculator.calculate_fee("30", 0)
