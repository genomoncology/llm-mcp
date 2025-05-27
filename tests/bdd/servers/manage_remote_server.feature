Feature: Add a remote MCP server and use it

  Background:
    Given I run "llm mcp servers add https://gitmcp.io/simonw/llm"

  Scenario: Check the add server output
    Then the output should contain "✔ added server 'gitmcp_llm' with 4 tools"

  Scenario: Check the server list
    When I run "llm mcp servers list"
    Then the output should contain "gitmcp_llm"

  Scenario: Check the server configuration
    When I run "llm mcp servers view gitmcp_llm"
    And I convert the output to a server config object
    Then the server config has 4 tools
    And "fetch_llm_documentation" has an input schema of "{}"
    And "search_llm_documentation" has "query" as a required parameter
