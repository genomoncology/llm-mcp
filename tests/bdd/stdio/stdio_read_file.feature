Feature: Read secret file via stdio MCP through CLI
  Background:
    Given an empty MCP config directory
    And the desktop-commander server is registered

  Scenario: LLM lists all of desktop-commander tools
    When I run "llm tools"
    Then the output contains "list_directory"
    And the output contains "read_file"

  Scenario: LLM lists the current working directory
    When I run "llm prompt -T list_directory -m gpt-4.1 'List the files in $data_dir.'"
    Then the output contains "secret.txt"

  Scenario: LLM reads secret.txt content
    When I run "llm prompt -T read_file -m gpt-4.1 'Read the secret.txt found in $data_dir.'"
    Then the output contains the secret text
