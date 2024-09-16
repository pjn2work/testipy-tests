Feature: Showing off behave (tutorial01)

  Background:
      Given we have behave installed

  Scenario: Simple test
    Then behave will test it for us.

  @my_scenario_tag_01
  Scenario Outline: Run D2 for: <Index> and <Desc>
      When we implement a test 5
      Then behave will test it for us! <Index> and <Desc>

    Examples: table 1
        | Index | Desc |
        | 4     | val4 |
        | 7     | val7 |
