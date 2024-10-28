Feature: PetStore

  Background:
    Given the base url is https://petstore3.swagger.io/api/v3/pet/


  Scenario: Create valid pet - YAML
    And I have the following YAML data, as data
      """
      id: 17
      name: Sissi
      category:
        id: 1
        name: Dogs
      photoUrls:
        - ""
      tags:
        - id: 0
          name: Schnauzer
        - id: 0
          name: mini
      status: available
      """
    When post data to pet store, I receive a 200 status code
    Then I can get the data pet from store, and receive a 200 status code


  Scenario: Create valid pet - JSON
    And I have the following JSON data, as data
      """
      {
        "id": 18,
        "name": "Sissi 2",
        "category": {
          "id": 1,
          "name": "Dogs"
        },
        "photoUrls": [
          ""
        ],
        "tags": [
          {
            "id": 0,
            "name": "Schnauzer"
          },
          {
            "id": 0,
            "name": "mini"
          }
        ],
        "status": "available"
      }
      """
    When post data to pet store, I receive a 200 status code
    Then I can get the data pet from store, and receive a 200 status code


  Scenario: Create invalid pet
    And I have the following YAML data, as data
      """
      name: Another Sissi
      """
    When post data to pet store, I receive a 500 status code
    Then do nothing
