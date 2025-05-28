Feature: Wrap tools from both HTTP and stdio MCP servers

  Background:
    Given the desktop-commander and simon/llm tools are loaded

  Scenario: Each wrapped tool exposes the required arguments
    When I collect the input-schemas of every wrapped tool
    Then the "search_llm_documentation" tool has a required "query" parameter
    And the "read_file" tool has a required "path" parameter

  Scenario: Retrieve pelican joke from secret.txt and search punchline from simonw/llm
    When the assistant reads the secret joke and finds its punchline
    Then the punchline is exactly "Because they always have a big bill!"
