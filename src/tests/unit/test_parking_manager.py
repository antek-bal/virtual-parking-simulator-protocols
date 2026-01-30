import pytest
from datetime import datetime


class TestParkingManager:
    def test_entry_not_valid_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_entry("PL", "GD12", 3)

    def test_entry_not_valid_floor(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_entry("PL", "GD12345", 5)

    def test_saving_to_dict(self, parking_manager, mocker):
        time = datetime(2026, 1, 29, 22, 46, 17)

        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = time

        assert parking_manager.register_entry("PL", "GD5P227", 3) == True
        assert parking_manager.active_parkings["GD5P227"]["entry_time"] == time
        assert parking_manager.active_parkings["GD5P227"]["floor"] == 3

    def test_get_payment_info_wrong_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.get_payment_info("GD5P227")

    def test_get_payment_info_success(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 1, 10, 00, 00)

        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 0)

        leave_time = datetime(2026, 1, 1, 11, 30, 00)

        mock_datetime.now.return_value = leave_time

        data = parking_manager.get_payment_info("GD5P227")

        assert data["registration_no"] == "GD5P227"
        assert data["fee"] == 3.0
        assert data["minutes"] == 90

    def test_exit_invalid_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_exit("GD5P227")

    def test_exit_success(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)

        assert parking_manager.register_exit("GD5P227") == True
        assert len(parking_manager.active_parkings) == 0

