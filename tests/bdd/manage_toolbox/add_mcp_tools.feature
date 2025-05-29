Feature: Add MCP tools to toolboxes

  Background:
    Given I run "llm mcp servers add --exist-ok 'npx @wonderwhy-er/desktop-commander'"
    And I run "llm mcp servers add --exist-ok 'https://gitmcp.io/simonw/llm'"
    And I run "llm mcp toolboxes add FileOps --description 'File operations'"

  Scenario: Add MCP tool to toolbox
    When I run "llm mcp toolboxes add-tool FileOps --mcp desktop_commander/read_file"
    Then the output should contain "✔ added tool 'read_file' to toolbox 'FileOps'"

  Scenario: Add MCP tool with custom name and description
    When I run "llm mcp toolboxes add-tool FileOps --mcp desktop_commander/list_directory --name list_files --description 'List files in a directory'"
    Then the output should contain "✔ added tool 'list_files' to toolbox 'FileOps'"
    When I run "llm mcp toolboxes view FileOps --json"
    And I convert the output to a toolbox config object
    Then the toolbox has tool "list_files" with description "List files in a directory"

  Scenario: Add non-existent MCP tool
    When I try to run "llm mcp toolboxes add-tool FileOps --mcp fake_server/fake_tool"
    Then it should fail with "Server 'fake_server' not found"

  Scenario: Add tool from non-existent server
    When I try to run "llm mcp toolboxes add-tool FileOps --mcp desktop_commander/non_existent_tool"
    Then it should fail with "Tool 'non_existent_tool' not found in server 'desktop_commander'"
