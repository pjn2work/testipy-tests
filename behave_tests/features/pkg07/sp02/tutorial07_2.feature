@my_feature_tag_07_2
Feature: Tutorial07_2


Scenario: Get Value from before_all context
    Then variable var07_0 from context has value TUTORIAL_07


Scenario: Get Value from package context - Fail
    Then variable var07_1 from context has value Fail, no attribute var_07_1


Scenario: Save Value in context
    When save text This is my text into context as var07_2
    Then variable var07_2 from context has value This is my text
