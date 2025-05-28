Feature: Use remote gitmcp/llm tools

  Background:
    Given I run "llm mcp servers add --exist-ok 'https://gitmcp.io/simonw/llm'"

  Scenario: Search documentation via search_llm_documentation tool
    When I run "llm prompt -m gpt-4.1-mini -T search_llm_code -T fetch_generic_url_content "Find the 2 aliases of gpt-3.5-turbo-16k in the simonw/llm repo.""
    Then the output should contain "chatgpt-16k"
    Then the output should contain "3.5-16k"
