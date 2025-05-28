Feature: Remove tools from toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp toolboxes add FileTools"
    And I run "llm mcp toolboxes add-tool FileTools --mcp desktop_commander/read_file"
    And I run "llm mcp toolboxes add-tool FileTools --mcp desktop_commander/write_file"

  Scenario: Remove tool from toolbox
    When I run "llm mcp toolboxes remove-tool FileTools read_file"
    Then the output should contain "✔ removed tool 'read_file' from toolbox 'FileTools'"
    When I run "llm mcp toolboxes view FileTools --json"
    And I convert the output to a toolbox config object
    Then the toolbox config has 1 tools

  Scenario: Remove non-existent tool
    When I try to run "llm mcp toolboxes remove-tool FileTools fake_tool"
    Then it should fail with "Tool 'fake_tool' not found in toolbox 'FileTools'"
