Feature: Create and manage toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp servers add --exist-ok 'https://gitmcp.io/simonw/llm'"

  Scenario: Create a new toolbox
    When I run "llm mcp toolboxes add data_analysis --description 'Tools for analyzing data'"
    Then the output should contain "✔ created toolbox 'data_analysis'"

  Scenario: Create toolbox with invalid name
    When I try to run "llm mcp toolboxes add data-analysis"
    Then it should fail with "Invalid toolbox name"

  Scenario: Create duplicate toolbox
    Given I run "llm mcp toolboxes add test_box"
    When I try to run "llm mcp toolboxes add test_box"
    Then it should fail with "Toolbox 'test_box' already exists"

  Scenario: List toolboxes
    Given I run "llm mcp toolboxes add analytics"
    And I run "llm mcp toolboxes add research --description 'Research tools'"
    When I run "llm mcp toolboxes list"
    Then the output should contain "analytics"
    And the output should contain "research"

  Scenario: View toolbox details
    Given I run "llm mcp toolboxes add my_tools --description 'My custom tools'"
    When I run "llm mcp toolboxes view my_tools --json"
    And I convert the output to a toolbox config object
    Then the toolbox config has name "my_tools"
    And the toolbox config has description "My custom tools"
    And the toolbox config has 0 tools
