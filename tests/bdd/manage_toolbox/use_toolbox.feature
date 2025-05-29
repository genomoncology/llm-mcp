Feature: Use toolboxes in prompts

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add FileReader"
    And I run "llm mcp toolboxes add-tool FileReader --mcp desktop_commander/read_file"
    And I run "llm mcp toolboxes set-default FileReader"

  Scenario: List tools shows toolbox
    When I run "llm tools"
    Then the output should contain "FileReader:"
    And the output should contain "read_file"

  Scenario: Clear default toolbox
    When I run "llm mcp toolboxes clear-default"
    Then the output should contain "✔ cleared default toolbox"
    When I run "llm tools"
    Then the output should contain "read_file(**kwargs: Any) -> Any (plugin: mcp)"
    And the output should contain "(plugin: mcp)"
