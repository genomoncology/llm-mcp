Feature: Add a new MCP server through the CLI

  As a CLI user I want to add a remote MCP server once and cache its tool list
  So that later commands can work offline without re-hitting the network

  Scenario: Add the simonw/llm server
    Given an empty MCP config directory
    When I run "llm_mcp add https://gitmcp.io/simonw/llm"
    And load the output server manifest should be "gitmcp_llm.json"
    Then the output should contain "✔ added server 'gitmcp_llm' with 4 tools"
    And "fetch_llm_documentation" lacks annotations or input schema
    And "search_llm_documentation" has "query" as a required parameter
