import requests

class VehicleValidator()
    def __init__(self, URL):
        self.URL = "https://api.cepik.gov.pl/pojazdy"

    def validate(self, country_abbreviation, registration_no):
        if country_abbreviation != "PL":
            return True

        response = requests.get(f"{self.URL}/{registration_no}")


