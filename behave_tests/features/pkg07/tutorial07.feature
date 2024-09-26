@my_feature_tag_07
Feature: Tutorial07

    feature description
    for these 2 tests


Scenario: Log messages
    This is a multiline
    scenario description

    Given send message to stdout
    And send message to stderr
    And log message to logger


Scenario: Start independent test
    When this test is running
    Then a new test manually created is created
    And a new test manually created is created but not ended
