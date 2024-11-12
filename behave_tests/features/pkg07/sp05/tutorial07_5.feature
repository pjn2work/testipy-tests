@my_feature_tag_07_5
@setup.sftp:cli2
Feature: Tutorial07_5


Scenario: Save Value in context
    When save text This is my text into context as var07_5
    Then variable var07_5 from context has value This is my text
