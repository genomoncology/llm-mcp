Feature: Validate toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add test_box"
    And I run "llm mcp toolboxes add-tool test_box --mcp desktop_commander/read_file"

  Scenario: Validate a healthy toolbox
    When I run "llm mcp toolboxes validate test_box"
    Then the output should contain "✔ Toolbox 'test_box' - No issues found"
    And the output should contain "Summary: All toolboxes are valid"

  Scenario: Validate a toolbox with a missing server
    Given I run "llm mcp servers add --manifest $data_dir/test_server.json --exist-ok"
    And I run "llm mcp toolboxes add broken_box"
    And I run "llm mcp toolboxes add-tool broken_box --mcp test_server/test_tool"
    And I run "llm mcp servers remove test_server"
    When I run "llm mcp toolboxes validate broken_box"
    Then the output should contain "⚠ Toolbox 'broken_box' - 1 issue(s) found"
    And the output should contain "Server 'test_server' not found"

  Scenario: Fix a toolbox with a missing server
    Given I run "llm mcp servers add --manifest $data_dir/test_server.json --exist-ok"
    And I run "llm mcp toolboxes add broken_box"
    And I run "llm mcp toolboxes add-tool broken_box --mcp test_server/test_tool"
    And I run "llm mcp servers remove test_server"
    When I run "llm mcp toolboxes validate broken_box --fix --force"
    Then the output should contain "✓ Fixed: Server 'test_server' not found"
    And the output should contain "✓ Removed empty toolbox 'broken_box'"
    When I run "llm mcp toolboxes list"
    Then the output should not contain "broken_box"

  Scenario: Validate all toolboxes
    Given I run "llm mcp toolboxes add healthy_box"
    And I run "llm mcp toolboxes add-tool healthy_box --mcp desktop_commander/read_file"
    And I run "llm mcp servers add --manifest $data_dir/test_server.json --exist-ok"
    And I run "llm mcp toolboxes add broken_box"
    And I run "llm mcp toolboxes add-tool broken_box --mcp test_server/test_tool"
    And I run "llm mcp servers remove test_server"
    When I run "llm mcp toolboxes validate"
    Then the output should contain "✔ Toolbox 'test_box' - No issues found"
    And the output should contain "✔ Toolbox 'healthy_box' - No issues found"
    And the output should contain "⚠ Toolbox 'broken_box' - 1 issue(s) found"
