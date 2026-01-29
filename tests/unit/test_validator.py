class TestVehicleValidator:
    def test_country_not_poland(self, vehicle_validator):
        assert vehicle_validator.validate("UA", "XK23456") == True

    def test_no_registration(self, vehicle_validator):
        assert vehicle_validator.validate("PL", "  ") == False

    def test_wrong_registration_type(self, vehicle_validator):
        assert vehicle_validator.validate("PL", 1234567) == False

    def test_standard_registration_success(self, vehicle_validator):
        assert vehicle_validator.validate("PL", "GD5P227") == True

    def test_standard_registration_failure(self, vehicle_validator):
        assert vehicle_validator.validate("PL", "GD12") == False

    def test_special_registration_success(self, vehicle_validator):
        assert vehicle_validator.validate("PL", "HPN123") == True

    def test_special_registration_failure(self, vehicle_validator):
        assert vehicle_validator.validate("PL", "HPN12") == False
