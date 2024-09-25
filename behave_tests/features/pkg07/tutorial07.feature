@my_feature_tag_07
Feature: tutorial07

    feature description
    for these 2 tests


Scenario: Log messages
    Given send message to stdout
    And send message to stderr
    And log message to logger


Scenario: Start independent test
    When this test is running
    Then a new test is created
