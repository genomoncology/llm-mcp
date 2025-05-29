Feature: Create and manage toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp servers add --exist-ok 'https://gitmcp.io/simonw/llm'"

  Scenario: Create a new toolbox
    When I run "llm mcp toolboxes add DataAnalysis --description 'Tools for analyzing data'"
    Then the output should contain "✔ created toolbox 'DataAnalysis'"

  Scenario: Create toolbox with invalid name
    When I try to run "llm mcp toolboxes add data-analysis"
    Then it should fail with "Invalid toolbox name"

  Scenario: Create duplicate toolbox
    Given I run "llm mcp toolboxes add TestBox"
    When I try to run "llm mcp toolboxes add TestBox"
    Then it should fail with "Toolbox 'TestBox' already exists"

  Scenario: List toolboxes
    Given I run "llm mcp toolboxes add Analytics"
    And I run "llm mcp toolboxes add Research --description 'Research tools'"
    When I run "llm mcp toolboxes list"
    Then the output should contain "Analytics"
    And the output should contain "Research"

  Scenario: View toolbox details
    Given I run "llm mcp toolboxes add MyTools --description 'My custom tools'"
    When I run "llm mcp toolboxes view MyTools --json"
    And I convert the output to a toolbox config object
    Then the toolbox config has name "MyTools"
    And the toolbox config has description "My custom tools"
    And the toolbox config has 0 tools
