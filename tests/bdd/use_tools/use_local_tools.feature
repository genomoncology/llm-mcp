Feature: Use desktop‑commander tools

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"

  Scenario: Read secret.txt via read_file tool
    When I run "llm prompt -T read_file -m gpt-4.1-nano 'Display the text found in secret.txt in $data_dir.'"
    Then the output should contain the secret text exactly as written
