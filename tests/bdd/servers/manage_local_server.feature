Feature: Add a remote MCP server and use it

  Background:
    Given I run "llm mcp servers add "npx @wonderwhy-er/desktop-commander""

  Scenario: Check the add server output
    Then the output should contain "✔ added server 'desktop_commander' with 18 tools"

  Scenario: Check the server list
    When I run "llm mcp servers list"
    Then the output should contain "desktop_commander"

  Scenario: Check the server configuration
    When I run "llm mcp servers view desktop_commander"
    And I convert the output to a server config object
    Then the server config has 18 tools
    And "list_directory" has "path" as a required parameter
    And "read_file" has "path" as a required parameter
