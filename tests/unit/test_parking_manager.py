import pytest
from datetime import datetime
from src.app.models.parking import Vehicle, ActiveParking, ParkingHistory


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

    def test_saving_to_db(self, parking_manager, mocker):
        time = datetime(2026, 1, 29, 22, 46, 17)
        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = time

        assert parking_manager.register_entry("PL", "GD5P227", 3) is True

        db_record = parking_manager.db.query(ActiveParking).join(Vehicle).filter(
            Vehicle.registration_no == "GD5P227"
        ).first()

        assert db_record is not None
        assert db_record.entry_time == time
        assert db_record.floor == 3

    def test_get_payment_info_wrong_registration(self, parking_manager):
        with pytest.raises(ValueError):
            parking_manager.get_payment_info("PL", "GD5P227")

    def test_get_payment_info_success(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 1, 10, 0, 0)
        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 0)

        leave_time = datetime(2026, 1, 1, 11, 30, 0)
        mock_datetime.now.return_value = leave_time

        data = parking_manager.get_payment_info("PL", "GD5P227")

        assert data["country"] == "PL"
        assert data["registration_no"] == "GD5P227"
        assert data["fee"] == 6.0
        assert data["minutes"] == 90

    def test_pay_parking_fee_success(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 1, 10, 0, 0)
        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 0)

        payment_time = datetime(2026, 1, 1, 11, 30, 0)
        mock_datetime.now.return_value = payment_time

        res = parking_manager.pay_parking_fee("PL", "GD5P227", 6.0)
        assert res["status"] is True
        assert res["fee"] == 6.0
        assert res["payment_time"] == payment_time

    def test_exit_success(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)
        parking_manager.pay_parking_fee("PL", "GD5P227", 0.0)

        assert parking_manager.register_exit("PL", "GD5P227") is True

        active_exists = parking_manager.db.query(ActiveParking).join(Vehicle).filter(
            Vehicle.registration_no == "GD5P227"
        ).first()
        assert active_exists is None

    def test_saving_to_history(self, parking_manager, mocker):
        entry_time = datetime(2026, 1, 29, 10, 0, 0)
        mock_datetime = mocker.patch('src.app.services.parking_manager.datetime')
        mock_datetime.now.return_value = entry_time

        parking_manager.register_entry("PL", "GD5P227", 3)

        pay_time = datetime(2026, 1, 29, 11, 30, 0)
        mock_datetime.now.return_value = pay_time
        parking_manager.pay_parking_fee("PL", "GD5P227", 3.0)

        exit_time = datetime(2026, 1, 29, 11, 40, 0)
        mock_datetime.now.return_value = exit_time
        parking_manager.register_exit("PL", "GD5P227")

        history_record = parking_manager.db.query(ParkingHistory).join(Vehicle).filter(
            Vehicle.registration_no == "GD5P227"
        ).first()

        assert history_record.entry_time == entry_time
        assert history_record.exit_time == exit_time
        assert history_record.floor == 3
        assert history_record.fee == 3.0

    def test_change_floor_valid(self, parking_manager):
        parking_manager.register_entry("PL", "GD5P227", 0)
        assert parking_manager.change_vehicle_floor("PL", "GD5P227", 1) is True

        active = parking_manager.db.query(ActiveParking).join(Vehicle).filter(
            Vehicle.registration_no == "GD5P227"
        ).first()
        assert active.floor == 1