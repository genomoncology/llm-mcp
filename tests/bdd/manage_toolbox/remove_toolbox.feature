Feature: Remove toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add TestBox"
    And I run "llm mcp toolboxes add-tool TestBox --mcp desktop_commander/read_file"

  Scenario: Remove a toolbox
    When I run "llm mcp toolboxes remove TestBox --force"
    Then the output should contain "✔ removed toolbox 'TestBox'"
    When I run "llm mcp toolboxes list"
    Then the output should not contain "TestBox"

  Scenario: Remove non-existent toolbox
    When I try to run "llm mcp toolboxes remove NonExistent"
    Then it should fail with "Toolbox 'NonExistent' not found"

  Scenario: Remove default toolbox with confirmation
    Given I run "llm mcp toolboxes set-default TestBox"
    When I run "llm mcp toolboxes remove TestBox --force"
    Then the output should contain "✔ removed toolbox 'TestBox'"
    When I run "llm mcp toolboxes list"
    Then the output should contain "No toolboxes found"
