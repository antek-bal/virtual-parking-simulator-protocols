Feature: Parking Cycle

  Scenario: Driver pays for parking and exits within the 15-minute limit
    Given Active parkings is empty
    When Vehicle from "PL" with registration number "GD5P227" has entered the parking lot on floor 0
    Then Number of active parkings equals 1
    And 90 minutes have passed since the entry time
    When Driver makes a card payment of 6.0
    And Driver attempts to exit 10 minutes after paying
    Then The system should remove the vehicle from the active parkings list
    And Save the session information in the history
