import pytest
from datetime import datetime


class TestParkingManager:
    def test_entry_not_valid_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_entry("PL", "GD12", 3)

    def test_entry_not_valid_floor(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_entry("PL", "GD12345", 5)

    def test_entry_same_vehicle_id(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 3)
        with pytest.raises(ValueError):
            parking_manager.register_entry("PL", "GD5P227", 0)

    def test_saving_to_dict(self, parking_manager, mocker):
        time = datetime(2026, 1, 29, 22, 46, 17)

        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = time

        assert parking_manager.register_entry("PL", "GD5P227", 3) == True
        assert parking_manager.active_parkings["PL_GD5P227"]["entry_time"] == time
        assert parking_manager.active_parkings["PL_GD5P227"]["floor"] == 3

    def test_get_payment_info_wrong_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.get_payment_info("PL", "GD5P227")

    def test_get_payment_info_success(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 1, 10, 00, 00)

        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 0)

        leave_time = datetime(2026, 1, 1, 11, 30, 00)

        mock_datetime.now.return_value = leave_time

        data = parking_manager.get_payment_info("PL", "GD5P227")

        assert data["country"] == "PL"
        assert data["registration_no"] == "GD5P227"
        assert data["fee"] == 6.0
        assert data["minutes"] == 90

    def test_exit_invalid_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.register_exit("PL", "GD5P227")

    def test_exit_success(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)

        assert parking_manager.register_exit("PL", "GD5P227") == True
        assert len(parking_manager.active_parkings) == 0

    def test_saving_to_history(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 29, 10, 00, 00)

        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 3)

        exit_time = datetime(2026, 1, 29, 11, 30, 00)

        mock_datetime.now.return_value = exit_time

        parking_manager.register_exit("PL", "GD5P227")

        assert parking_manager.history["PL_GD5P227"][0]["entry_time"] == entry_time
        assert parking_manager.history["PL_GD5P227"][0]["exit_time"] == exit_time
        assert parking_manager.history["PL_GD5P227"][0]["floor"] == 3
        assert parking_manager.history["PL_GD5P227"][0]["fee"] == 3.0

    def test_multiple_parkings_in_history(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)
        parking_manager.register_exit("PL", "GD5P227")

        parking_manager.register_entry("PL", "GD5P227", 1)
        parking_manager.register_exit("PL", "GD5P227")

        assert len(parking_manager.history["PL_GD5P227"]) == 2

    def test_change_floor_invalid_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.change_vehicle_floor("PL", "GD5P227", 0)

    def test_change_floor_invalid_floor(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)
        with pytest.raises(ValueError):
            parking_manager.change_vehicle_floor("PL", "GD5P227", 5)

    def test_change_floor_valid(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)

        assert parking_manager.change_vehicle_floor("PL", "GD5P227", 1) == True
        assert parking_manager.active_parkings["PL_GD5P227"]["floor"] == 1


