Feature: Use remote gitmcp/llm tools

  Background:
    Given I run "llm mcp servers add --exist-ok https://gitmcp.io/simonw/llm"
    And I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"


  Scenario: Multi-tool prompt
    When I run "llm prompt -m gpt-4.1 -T read_file -T search_llm_code -T fetch_generic_url_content "Read the joke in tests/data/joke.txt. Then search using that exact joke in the simonw/llm repo, then display the punchline found after fetching the content.""
    Then the output should contain "big bill"
