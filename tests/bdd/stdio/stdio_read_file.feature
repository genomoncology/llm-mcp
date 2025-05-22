Feature: Read secret file via stdio MCP
  Background:
    Given the desktop-commander is available with directory access

  Scenario: LLM lists the current working directory
    When the assistant is prompted to list the current directory
    Then the listing response contains "secret.txt"

  Scenario: LLM reads secret.txt content
    When the assistant is asked to read the secret.txt file
    Then the assistant reply contains the secret text
