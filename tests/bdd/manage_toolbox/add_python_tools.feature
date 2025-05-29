Feature: Add Python functions and classes to toolboxes

  Background:
    Given I run "llm mcp toolboxes add Utils --description 'Utility functions'"

  Scenario: Add inline Python function
    When I run "llm mcp toolboxes add-tool Utils --function 'def double(x: int) -> int: return x * 2 # Double a number'"
    Then the output should contain "✔ added tool 'double' to toolbox 'Utils'"

  Scenario: Add Python function from file
    Given a file "math_tools.py" with content:
      """
      def calculate_average(numbers: list[float]) -> float:
          '''Calculate the average of a list of numbers'''
          return sum(numbers) / len(numbers) if numbers else 0

      def calculate_sum(numbers: list[float]) -> float:
          '''Calculate the sum of a list of numbers'''
          return sum(numbers)
      """
    When I run "llm mcp toolboxes add-tool Utils --function $data_dir/math_tools.py --function-name calculate_average"
    Then the output should contain "✔ added tool 'calculate_average' to toolbox 'Utils'"

  Scenario: Add Python function with custom name
    When I run "llm mcp toolboxes add-tool Utils --function 'def add(a: int, b: int) -> int: return a + b' --name add_numbers --description 'Add two numbers together'"
    Then the output should contain "✔ added tool 'add_numbers' to toolbox 'Utils'"
