from typing import List


class VehicleValidator:
    def __init__(self, basic_letters: List[str], special_letters: List[str]):
        self.basic_letters = basic_letters
        self.special_letters = special_letters

    def validate(self, country_abbreviation: str, registration_no: str) -> bool:
        if country_abbreviation != "PL":
            return True

        if not registration_no or not isinstance(registration_no, str):
            return False

        first_letter = registration_no[0]

        if first_letter in self.basic_letters:
            return 5 <= len(registration_no) <= 8

        if first_letter in self.special_letters:
            return len(registration_no) >= 6

        return False
