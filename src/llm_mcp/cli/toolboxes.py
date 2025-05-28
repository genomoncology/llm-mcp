"""CLI commands for toolbox management."""

import ast
from pathlib import Path

import click

from llm_mcp import store
from llm_mcp.cli.main import mcp
from llm_mcp.schema import ToolboxConfig, ToolboxTool


@mcp.group()
def toolboxes():
    """Manage custom LLM toolboxes."""


@toolboxes.command(name="add")
@click.argument("name")
@click.option("--description", help="Toolbox description")
def add_toolbox(name: str, description: str | None):
    """Create a new toolbox."""
    # Validate toolbox name
    if not name[0].isupper():
        raise click.ClickException(
            "Toolbox names must start with a capital letter"
        )

    # Check if toolbox already exists
    if store.load_toolbox(name):
        raise click.ClickException(f"Toolbox '{name}' already exists")

    # Create and save toolbox
    toolbox = ToolboxConfig(
        name=name,
        description=description,
    )
    store.save_toolbox(toolbox)
    click.echo(f"✔ created toolbox '{name}'")


@toolboxes.command(name="add-tool")
@click.argument("toolbox_name")
@click.option("--mcp", help="MCP tool reference: server_name/tool_name")
@click.option("--function", help="Python function code or file path")
@click.option("--function-name", help="Function name to extract from file")
@click.option("--toolbox-class", help="Python Toolbox class code or file path")
@click.option("--name", help="Override tool name")
@click.option("--description", help="Override tool description")
def add_tool_to_toolbox(
    toolbox_name: str,
    mcp: str | None = None,
    function: str | None = None,
    function_name: str | None = None,
    toolbox_class: str | None = None,
    name: str | None = None,
    description: str | None = None,
):
    """Add a tool to a toolbox."""
    # Load toolbox
    config = store.load_toolbox(toolbox_name)
    if config is None:
        raise click.ClickException(f"Toolbox '{toolbox_name}' not found")

    # Validate options
    source_count = sum(x is not None for x in [mcp, function, toolbox_class])
    if source_count != 1:
        raise click.ClickException(
            "Exactly one of --mcp, --function, or --toolbox-class must be specified"
        )

    # Create tool based on source type
    if mcp:
        tool = _create_mcp_tool(mcp, name, description)
    elif function:
        tool = _create_function_tool(
            function, function_name, name, description
        )
    else:  # toolbox_class
        tool = _create_toolbox_class_tool(toolbox_class, name, description)

    # Add tool to config
    config.tools.append(tool)

    # Save updated config
    store.save_toolbox(config)

    # Display success message
    tool_name = tool.name or tool.tool_name or tool.function_name or "tool"
    click.secho(
        f"✔ added tool '{tool_name}' to toolbox '{toolbox_name}'", fg="green"
    )


def _create_mcp_tool(
    mcp: str, name: str | None, description: str | None
) -> ToolboxTool:
    """Create an MCP tool reference."""
    # Validate MCP reference format
    server_name, tool_name = _parse_mcp_reference(mcp)

    # Verify server exists
    server_config = store.load_server(server_name)
    if server_config is None:
        raise click.ClickException(f"Server '{server_name}' not found")

    # Verify tool exists in server
    if not any(t.name == tool_name for t in server_config.tools):
        raise click.ClickException(
            f"Tool '{tool_name}' not found in server '{server_name}'"
        )

    return ToolboxTool(
        source_type="mcp",
        mcp_ref=mcp,
        code=None,
        function_name=None,
        name=name,
        description=description,
    )


def _create_function_tool(
    function: str,
    function_name: str | None,
    name: str | None,
    description: str | None,
) -> ToolboxTool:
    """Create a Python function tool."""
    # Read code from file if it's a path
    code = _read_code_or_path(function)

    # Validate syntax
    try:
        compile(code, "<function>", "exec")
    except SyntaxError as e:
        raise click.ClickException(
            f"Syntax error in function code: {e}"
        ) from e

    # Extract specific function if requested
    if function_name:
        code = _extract_specific_function(code, function_name)

    # Extract function name if not specified
    if not function_name and not name:
        function_name = _extract_function_name(code)

    return ToolboxTool(
        source_type="function",
        mcp_ref=None,
        code=code,
        function_name=function_name,
        name=name,
        description=description,
    )


def _create_toolbox_class_tool(
    toolbox_class: str | None,
    name: str | None,
    description: str | None,
) -> ToolboxTool:
    """Create a Toolbox class tool."""
    if not toolbox_class:
        raise click.ClickException("Toolbox class code or path is required")

    # Similar to _create_function_tool but for classes
    code = _read_code_or_path(toolbox_class)

    # Validate syntax
    try:
        compile(code, "<toolbox>", "exec")
    except SyntaxError as e:
        raise click.ClickException(
            f"Syntax error in toolbox class code: {e}"
        ) from e

    return ToolboxTool(
        source_type="toolbox_class",
        mcp_ref=None,
        code=code,
        function_name=None,
        name=name,
        description=description,
    )


def _read_code_or_path(code_or_path: str) -> str:
    """Read code from a file path or return the string directly."""
    path = Path(code_or_path)
    if path.exists() and path.is_file():
        return path.read_text()
    return code_or_path


def _extract_function_name(code: str) -> str:
    """Extract the first function name from Python code."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except SyntaxError as e:
        raise click.ClickException(
            f"Syntax error in function code: {e}"
        ) from e

    raise click.ClickException("No function found in the provided code")


def _extract_specific_function(code: str, function_name: str) -> str:
    """Extract a specific function from Python code."""
    try:
        module = ast.parse(code)

        # Find the specified function in the module
        function_def = None
        for node in ast.walk(module):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == function_name
            ):
                function_def = node
                break

        if not function_def:
            raise click.ClickException(
                f"Function '{function_name}' not found in provided code"
            )

        # Extract just this function's code
        function_lines = code.splitlines()
        start_line = function_def.lineno - 1
        end_line = function_def.end_lineno
        return "\n".join(function_lines[start_line:end_line])

    except SyntaxError as e:
        raise click.ClickException(
            f"Syntax error in function code: {e}"
        ) from e


@toolboxes.command(name="remove-tool")
@click.argument("toolbox_name")
@click.argument("tool_name")
def remove_tool_from_toolbox(toolbox_name: str, tool_name: str):
    """Remove a tool from a toolbox."""
    # Load toolbox
    toolbox = store.load_toolbox(toolbox_name)
    if not toolbox:
        raise click.ClickException(f"Toolbox '{toolbox_name}' not found")

    # Find and remove tool
    original_count = len(toolbox.tools)
    toolbox.tools = [
        t
        for t in toolbox.tools
        if (t.name or t.tool_name or t.function_name) != tool_name
    ]

    if len(toolbox.tools) == original_count:
        raise click.ClickException(
            f"Tool '{tool_name}' not found in toolbox '{toolbox_name}'"
        )

    # Save updated toolbox
    store.save_toolbox(toolbox)
    click.echo(f"✔ removed tool '{tool_name}' from toolbox '{toolbox_name}'")


@toolboxes.command(name="list")
@click.option("--json", is_flag=True, help="Output as JSON")
def list_toolboxes(json: bool):
    """List all toolboxes."""
    toolbox_names = store.list_toolboxes()

    if json:
        import json as json_module

        result = []
        for name in toolbox_names:
            toolbox = store.load_toolbox(name)
            if toolbox:
                result.append(toolbox.model_dump())
        click.echo(json_module.dumps(result, indent=2))
    else:
        if not toolbox_names:
            click.echo(
                "No toolboxes found. Create one with: llm mcp toolboxes add <name>"
            )
            return

        default = store.get_default_toolbox()
        for name in sorted(toolbox_names):
            toolbox = store.load_toolbox(name)
            desc = (
                f" - {toolbox.description}"
                if toolbox and toolbox.description
                else ""
            )
            default_marker = " (default)" if name == default else ""
            click.echo(f"{name}{default_marker}{desc}")


@toolboxes.command(name="view")
@click.argument("name")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def view_toolbox(name: str, output_json: bool):
    """View toolbox details."""
    toolbox = store.load_toolbox(name)
    if not toolbox:
        raise click.ClickException(f"Toolbox '{name}' not found")

    if output_json:
        click.echo(toolbox.model_dump_json(indent=2))
    else:
        click.echo(f"Toolbox: {toolbox.name}")
        if toolbox.description:
            click.echo(f"Description: {toolbox.description}")

        if not toolbox.tools:
            click.echo("No tools added yet.")
            click.echo("Add tools with: llm mcp toolboxes add-tool")
        else:
            click.echo(f"Tools ({len(toolbox.tools)}):")
            for tool in toolbox.tools:
                tool_name = tool.name or tool.tool_name or tool.function_name
                source = (
                    f"[MCP: {tool.mcp_ref}]" if tool.mcp_ref else "[Function]"
                )
                desc = f" - {tool.description}" if tool.description else ""
                click.echo(f"  - {tool_name} {source}{desc}")


@toolboxes.command(name="set-default")
@click.argument("name")
def set_default_toolbox(name: str):
    """Set a toolbox as the default for LLM."""
    # Check if toolbox exists
    if not store.load_toolbox(name):
        raise click.ClickException(f"Toolbox '{name}' not found")

    # Set as default
    store.set_default_toolbox(name)
    click.echo(f"✔ set '{name}' as default toolbox")


@toolboxes.command(name="clear-default")
def clear_default_toolbox():
    """Clear the default toolbox setting."""
    store.set_default_toolbox(None)
    click.echo("✔ cleared default toolbox")


def _parse_mcp_reference(mcp_ref: str) -> tuple[str, str]:
    """Parse an MCP reference into server and tool names."""
    parts = mcp_ref.split("/")
    if len(parts) != 2:
        raise click.ClickException(
            f"Invalid MCP reference: {mcp_ref}. Expected format: server_name/tool_name"
        )
    return parts[0], parts[1]
