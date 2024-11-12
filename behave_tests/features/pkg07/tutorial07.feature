@my_feature_tag_07
@setup.db:cli3
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


Scenario: Get Value from before_all context
    Then variable var07_0 from context has value TUTORIAL_07


Scenario: Save Value in context
    When save text This is my text into context as var07_1
    Then variable var07_1 from context has value This is my text
