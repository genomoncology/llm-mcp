Feature: Using asynchronous tools
  As a developer
  I want to use asynchronous functions in my tools
  So that I can perform non-blocking operations

  Scenario: Create and use an async tool
    Given I run "llm mcp toolboxes add AsyncToolbox"
    And I create a file at "async_tool.py" with the following content:
      """
      import asyncio

      async def fetch_data(delay: float = 0.1):
          \"\"\"Simulates fetching data with the given delay.\"\"\"
          await asyncio.sleep(delay)
          return f"Data fetched after {delay} seconds"
      """
    When I run "llm mcp toolboxes add-tool AsyncToolbox --function async_tool.py --function-name fetch_data"
    Then the output should contain "added tool 'fetch_data' to toolbox 'AsyncToolbox'"
    When I run "llm prompt 'Call AsyncToolbox.fetch_data with a delay of 0.2 seconds and show the result'"
    Then the output should contain "Data fetched after 0.2 seconds"
    And the output should not contain "coroutine object"
