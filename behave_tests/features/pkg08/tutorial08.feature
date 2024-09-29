Feature: Tutorial08

  Background:
    Given we have behave installed

  Scenario: Table test
    Then behave table test step
      | column_A | column_B |
      | field 1  | string   |
      | field 2  | integer  |
      | field 3  | float    |
