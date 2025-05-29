Feature: Remove toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add test_box"
    And I run "llm mcp toolboxes add-tool test_box --mcp desktop_commander/read_file"

  Scenario: Remove a toolbox
    When I run "llm mcp toolboxes remove test_box --force"
    Then the output should contain "✔ removed toolbox 'test_box'"
    When I run "llm mcp toolboxes list"
    Then the output should not contain "test_box"

  Scenario: Remove non-existent toolbox
    When I try to run "llm mcp toolboxes remove non_existent"
    Then it should fail with "Toolbox 'non_existent' not found"

  Scenario: Remove default toolbox with confirmation
    Given I run "llm mcp toolboxes set-default test_box"
    When I run "llm mcp toolboxes remove test_box --force"
    Then the output should contain "✔ removed toolbox 'test_box'"
    When I run "llm mcp toolboxes list"
    Then the output should contain "No toolboxes found"
