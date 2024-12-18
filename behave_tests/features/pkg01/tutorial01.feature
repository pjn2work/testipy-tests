Feature: Showing off behave (tutorial01)

  Background:
    Given we have behave installed


  @tc:200555
  Scenario: Table test with matplotlib and plotly graphs
    Then plot table having header at 1 row and index at 1 column
      | int      | int   | int      |
      | velocity | price | discount |
      | 10       | 10    | 1        |
      | 20       | 15    | 5        |
      | 30       | 18    | 8        |
      | 50       | 30    | 3        |
      | 80       | 40    | 4        |
      | 130      | 45    | 5        |


  @my_scenario_tag_01
  @tc:201750 @tc:201800
  Scenario Outline: Examples scenario for: <Index> and <Desc>
    When we implement a test 5
    Then behave will test it for us! <Index> and <Desc>

    @prefix:table_1
    Examples: table 1
      | Index | Desc |
      | 4     | val4 |
      | 7     | Fail |

    @prefix:table_2
    Examples: table 2
      | Index | Desc |
      | 1     | val1 |
      | 2     | val2 |


  Scenario: Test Context
    When save current datetime in context as test_started
    Then context has data in test_started
    When context clear data in test_started
    Then context has no data in test_started


  Scenario: Data validations
    And context clear data bucket
    When I have the following YAML data, as table1
      """
      - name: My Long Name
        age: 10
        size: 7.8
        human: true
        address:
          home: address 1
          office: address 2
        cars:
          - Volvo
          - Ferrari
        debts: null
        birth: 2003-11-13 23:59:30
        date1: 2003-11-13
        time1: 23:59:30
      """
    Then table table1 was already saved in context
    And data from table1, must have 1 entries
    And data from table1, must have the following types
      | column_name | column_type |
      | name        | string      |
      | age         | integer     |
      | size        | float       |
      | human       | boolean     |
      | address     | struct      |
      | cars        | list        |
      | debts       | string,none |
      | birth       | datetime    |
      | date1       | date        |
      | time1       | integer     |


  Scenario: Read resources file
    When read resources/demo.csv file as csv into file1
    Then data from file1, must have the following types
      | column_name | column_type |
      | Industry    | string      |
      | Year        | integer     |


  Scenario: Test with undefined steps - Fail
    When I have Undefined step
    Then do nothing
