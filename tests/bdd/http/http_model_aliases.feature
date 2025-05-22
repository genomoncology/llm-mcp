Feature: Fetch model aliases via HTTP MCP
  Scenario: Retrieve aliases for gpt-3.5-turbo-16k
    Given the HTTP tools for the simonw/llm repository are available
    When the assistant is asked for the aliases of "gpt-3.5-turbo-16k"
    Then the assistant returns aliases including "chatgpt-16k" and "3.5-16k"
