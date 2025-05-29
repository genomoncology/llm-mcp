Feature: Set and use default toolbox

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add analysis"
    And I run "llm mcp toolboxes add-tool analysis --mcp desktop_commander/read_file"

  Scenario: Set default toolbox
    When I run "llm mcp toolboxes set-default analysis"
    Then the output should contain "✔ set 'analysis' as default toolbox"

  Scenario: Clear default toolbox
    Given I run "llm mcp toolboxes set-default analysis"
    When I run "llm mcp toolboxes clear-default"
    Then the output should contain "✔ cleared default toolbox"

  Scenario: List tools shows only toolbox when default is set
    Given I run "llm mcp toolboxes set-default analysis"
    When I run "llm tools"
    Then the output should contain "analysis:"
    And the output should contain "read_file("
    And the output should not contain "list_directory("

  Scenario: List tools shows all server tools when no default
    Given I run "llm mcp toolboxes clear-default"
    When I run "llm tools"
    Then the output should contain "read_file(**kwargs: Any) -> Any (plugin: mcp)"
    And the output should contain "list_directory(**kwargs: Any) -> Any (plugin: mcp)"
