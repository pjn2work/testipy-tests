Feature: Showing off behave (tutorial01)

  Background:
    Given we have behave installed

  @tc:200555
  Scenario: Table test
    Then behave table test step
      | column_A | column_B |
      | field 1  | string   |
      | field 2  | integer  |
      | field 3  | float    |

  @my_scenario_tag_01
  @tc:201728
  Scenario Outline: Examples scenario for: <Index> and <Desc>
    When we implement a test 5
    Then behave will test it for us! <Index> and <Desc>

    @prefix:table_1
    Examples: table 1
      | Index | Desc |
      | 4     | val4 |
      | 7     | val7 |

    @prefix:table_2
    Examples: table 2
      | Index | Desc |
      | 1     | val1 |
      | 2     | val2 |
