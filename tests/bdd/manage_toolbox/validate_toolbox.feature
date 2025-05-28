Feature: Validate toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add TestBox"
    And I run "llm mcp toolboxes add-tool TestBox --mcp desktop_commander/read_file"

  Scenario: Validate a healthy toolbox
    When I run "llm mcp toolboxes validate TestBox"
    Then the output should contain "✔ Toolbox 'TestBox' - No issues found"
    And the output should contain "Summary: All toolboxes are valid"

  Scenario: Validate a toolbox with a missing server
    Given I run "llm mcp servers add --manifest $data_dir/test-server.json --exist-ok"
    And I run "llm mcp toolboxes add BrokenBox"
    And I run "llm mcp toolboxes add-tool BrokenBox --mcp test-server/test-tool"
    And I run "llm mcp servers remove test-server"
    When I run "llm mcp toolboxes validate BrokenBox"
    Then the output should contain "⚠ Toolbox 'BrokenBox' - 1 issue(s) found"
    And the output should contain "Server 'test-server' not found"

  Scenario: Fix a toolbox with a missing server
    Given I run "llm mcp servers add --manifest $data_dir/test-server.json --exist-ok"
    And I run "llm mcp toolboxes add BrokenBox"
    And I run "llm mcp toolboxes add-tool BrokenBox --mcp test-server/test-tool"
    And I run "llm mcp servers remove test-server"
    When I run "llm mcp toolboxes validate BrokenBox --fix --force"
    Then the output should contain "✓ Fixed: Server 'test-server' not found"
    And the output should contain "✓ Removed empty toolbox 'BrokenBox'"
    When I run "llm mcp toolboxes list"
    Then the output should not contain "BrokenBox"

  Scenario: Validate all toolboxes
    Given I run "llm mcp toolboxes add HealthyBox"
    And I run "llm mcp toolboxes add-tool HealthyBox --mcp desktop_commander/read_file"
    And I run "llm mcp servers add --manifest $data_dir/test-server.json --exist-ok"
    And I run "llm mcp toolboxes add BrokenBox"
    And I run "llm mcp toolboxes add-tool BrokenBox --mcp test-server/test-tool"
    And I run "llm mcp servers remove test-server"
    When I run "llm mcp toolboxes validate"
    Then the output should contain "✔ Toolbox 'TestBox' - No issues found"
    And the output should contain "✔ Toolbox 'HealthyBox' - No issues found"
    And the output should contain "⚠ Toolbox 'BrokenBox' - 1 issue(s) found"
