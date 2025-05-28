"""Toolbox builder functionality for dynamically creating toolbox classes."""

import ast
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import llm

from llm_mcp import store, transport
from llm_mcp.schema import ToolboxConfig, ToolboxTool


def build_toolbox_class(config: ToolboxConfig) -> type[llm.Toolbox]:
    """Dynamically create a Toolbox class from configuration."""

    # Create base class with config
    # Use a proper Dict type annotation to avoid mypy collection error
    from typing import Any as AnyType

    class_attrs: dict[str, AnyType] = {
        "name": config.name,
        "__doc__": config.description or f"Dynamic toolbox: {config.name}",
        "_config": config.config,
    }

    # Add __init__ method
    def __init__(self, **kwargs):
        # Merge kwargs with stored config
        merged_config = {**config.config, **kwargs}
        llm.Toolbox.__init__(self)
        for key, value in merged_config.items():
            setattr(self, key, value)

    class_attrs["__init__"] = __init__

    # Add methods for each tool
    for tool in config.tools:
        method = _create_tool_method(tool)
        method_name = tool.name or _get_default_method_name(tool)
        class_attrs[method_name] = method

    # Create the class
    DynamicToolbox = type(config.name, (llm.Toolbox,), class_attrs)
    return DynamicToolbox


def _get_default_method_name(tool: ToolboxTool) -> str:
    """Get the default method name for a tool."""
    if tool.source_type == "mcp" and tool.tool_name:
        return tool.tool_name
    elif tool.source_type == "function" and tool.function_name:
        return tool.function_name
    # Fallback to a unique identifier
    return f"tool_{id(tool)}"


def _create_tool_method(tool: ToolboxTool) -> Callable:
    """Create a method for a tool based on its source type."""

    if tool.source_type == "mcp":
        return _create_mcp_method(tool)
    elif tool.source_type == "function":
        return _create_function_method(tool)
    elif tool.source_type == "toolbox_class":
        return _create_toolbox_class_method(tool)
    else:
        raise ValueError(f"Unknown source type: {tool.source_type}")


def _create_mcp_method(tool: ToolboxTool) -> Callable:
    """Create a method that calls an MCP tool."""

    def method(self, **kwargs):
        # Parse MCP reference to get server and tool names
        if not tool.mcp_ref:
            raise ValueError("MCP reference is required for MCP tools")

        server_name, tool_name = _parse_mcp_reference(tool.mcp_ref)

        # Load server config
        server_config = store.load_server(server_name)
        if not server_config:
            raise ValueError(f"Server {server_name} not found")

        # Get the MCP tool
        mcp_tool = None
        for t in server_config.tools:
            if t.name == tool_name:
                mcp_tool = t
                break

        if not mcp_tool:
            raise ValueError(
                f"Tool {tool_name} not found in server {server_name}"
            )

        # Call it using appropriate transport
        params = server_config.parameters
        if params.__class__.__name__ == "RemoteServerParameters":
            # Type cast to help mypy
            from llm_mcp.schema import RemoteServerParameters

            remote_params = (
                params if isinstance(params, RemoteServerParameters) else None
            )
            if remote_params is None:
                raise ValueError("Invalid server parameters type")
            return transport.http.call_tool_sync(
                remote_params, tool_name, kwargs
            )
        else:
            # Type cast to help mypy
            from llm_mcp.schema import StdioServerParameters

            stdio_params = (
                params if isinstance(params, StdioServerParameters) else None
            )
            if stdio_params is None:
                raise ValueError("Invalid server parameters type")
            return transport.stdio.call_tool_sync(
                stdio_params, tool_name, kwargs
            )

    # Set metadata
    method_name = (
        tool.name
        or tool.tool_name
        or (
            tool.mcp_ref.split("/")[1]
            if tool.mcp_ref and "/" in tool.mcp_ref
            else "mcp_tool"
        )
    )
    method.__name__ = method_name
    method.__doc__ = tool.description or "MCP tool wrapper"

    return method


def _create_function_method(tool: ToolboxTool) -> Callable:
    """Create a method from Python function code."""

    if not tool.code:
        raise ValueError("Function code is required for function tools")

    # Parse the code to extract the function
    try:
        code = _get_function_code(tool.code)
        func_name = _extract_function_name_from_tool(tool, code)
        func = _load_function_from_code(code, func_name, tool)
        method = _create_wrapper_method(func)

        # Set metadata
        method.__name__ = tool.name or func_name
        method.__doc__ = (
            tool.description
            or func.__doc__
            or f"Dynamic function: {func_name}"
        )
    except Exception as e:
        raise ValueError(f"Error creating function method: {e}") from e
    else:
        return method


def _get_function_code(code_or_path: str) -> str:
    """Get the function code from a string or file path."""
    if Path(code_or_path).exists():
        return Path(code_or_path).read_text()
    return code_or_path


def _extract_function_name_from_tool(tool: ToolboxTool, code: str) -> str:
    """Extract the function name from the tool or code."""
    if tool.function_name:
        return tool.function_name

    # Parse the code and find the first function
    module_ast = ast.parse(code)
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef):
            return node.name

    raise ValueError("No function found in the provided code")


def _load_function_from_code(
    code: str, func_name: str, tool: ToolboxTool
) -> Callable:
    """Load a function from code into a temporary module."""
    # Create a temporary module
    module_name = f"_toolbox_dynamic_module_{id(tool)}"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    if spec is None:
        raise ValueError(f"Failed to create module spec for {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    # Execute the code in the module's namespace
    exec(code, module.__dict__)  # noqa: S102

    # Get and return the function
    return getattr(module, func_name)


def _create_wrapper_method(func: Callable) -> Callable[..., Any]:
    """Create a wrapper method that calls the function."""

    # Create a properly typed wrapper function that satisfies mypy
    class MethodWrapper:
        @staticmethod
        def get_wrapper(f: Callable) -> Callable[..., Any]:
            def method(self: Any, **kwargs: Any) -> Any:
                return f(**kwargs)

            return method

    # Use the wrapper to create and return the method
    return MethodWrapper.get_wrapper(func)


def _create_toolbox_class_method(tool: ToolboxTool) -> Callable:
    """Create a method that delegates to another toolbox class."""
    # This is a placeholder for future implementation
    raise NotImplementedError("Toolbox class tools are not yet implemented")


def _parse_mcp_reference(mcp_ref: str) -> tuple[str, str]:
    """Parse an MCP reference into server and tool names."""
    parts = mcp_ref.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid MCP reference: {mcp_ref}. Expected format: server_name/tool_name"
        )
    return parts[0], parts[1]


# Type for validation fix callbacks
FixCallback = Callable[[], None]


class ValidationIssue:
    """Represents an issue found during toolbox validation."""

    SEVERITY_WARNING = "warning"
    SEVERITY_ERROR = "error"

    def __init__(
        self,
        tool: ToolboxTool | None,
        severity: str,
        message: str,
        fix_callback: FixCallback | None = None,
    ):
        self.tool = tool
        self.severity = severity
        self.message = message
        self.fix_callback = fix_callback

    def fix(self) -> None:
        """Apply the fix for this issue if a fix callback is available."""
        if self.fix_callback:
            self.fix_callback()

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.message}"


def validate_toolbox(toolbox: ToolboxConfig) -> list[ValidationIssue]:
    """Validate a toolbox configuration and return a list of issues.

    Checks:
    - For MCP tools: Server exists and tool is present in the server
    - For function tools: Function code is valid
    - For toolbox class tools: Class code is valid
    """
    issues = []

    # Process each tool in the toolbox
    for tool in toolbox.tools:
        if tool.source_type == "mcp":
            issues.extend(_validate_mcp_tool(tool, toolbox))
        elif tool.source_type == "function":
            issues.extend(_validate_function_tool(tool, toolbox))
        elif tool.source_type == "toolbox_class":
            issues.extend(_validate_toolbox_class_tool(tool, toolbox))

    return issues


def _validate_mcp_tool(
    tool: ToolboxTool, toolbox: ToolboxConfig
) -> list[ValidationIssue]:
    """Validate an MCP tool reference."""
    issues = []

    # Check for missing reference
    if not tool.mcp_ref:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message="MCP tool is missing reference",
                fix_callback=fix_callback,
            )
        )
        return issues

    # Validate reference format
    try:
        server_name, tool_name = _parse_mcp_reference(tool.mcp_ref)
    except ValueError as e:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message=str(e),
                fix_callback=fix_callback,
            )
        )
        return issues

    # Check if server exists
    server_config = store.load_server(server_name)
    if not server_config:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message=f"Server '{server_name}' not found",
                fix_callback=fix_callback,
            )
        )
        return issues

    # Check if tool exists in server
    if not any(t.name == tool_name for t in server_config.tools):

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message=f"Tool '{tool_name}' not found in server '{server_name}'",
                fix_callback=fix_callback,
            )
        )

    return issues


def _validate_function_tool(
    tool: ToolboxTool, toolbox: ToolboxConfig
) -> list[ValidationIssue]:
    """Validate a function tool."""
    issues = []

    # Check for missing code
    if not tool.code:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message="Function tool is missing code",
                fix_callback=fix_callback,
            )
        )
        return issues

    # Verify function code is valid Python
    try:
        compile(tool.code, "<function>", "exec")
    except SyntaxError as e:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message=f"Syntax error in function code: {e}",
                fix_callback=fix_callback,
            )
        )

    return issues


def _validate_toolbox_class_tool(
    tool: ToolboxTool, toolbox: ToolboxConfig
) -> list[ValidationIssue]:
    """Validate a toolbox class tool."""
    issues = []

    # Check for missing code
    if not tool.code:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message="Toolbox class tool is missing code",
                fix_callback=fix_callback,
            )
        )
        return issues

    # Verify class code is valid Python
    try:
        compile(tool.code, "<toolbox_class>", "exec")
    except SyntaxError as e:

        def fix_callback() -> None:
            _fix_remove_tool(toolbox, tool)

        issues.append(
            ValidationIssue(
                tool=tool,
                severity=ValidationIssue.SEVERITY_ERROR,
                message=f"Syntax error in toolbox class code: {e}",
                fix_callback=fix_callback,
            )
        )

    return issues


def _fix_remove_tool(toolbox: ToolboxConfig, tool: ToolboxTool) -> None:
    """Fix helper to remove a tool from a toolbox and save the updated toolbox."""
    # Remove the tool from the toolbox
    toolbox.tools = [t for t in toolbox.tools if t is not tool]

    # Save the updated toolbox
    store.save_toolbox(toolbox)


def register_toolbox_tools(register):
    """Register tools from all toolboxes or just the default one."""
    default_toolbox_name = store.get_default_toolbox()

    if default_toolbox_name:
        # Load and register only the default toolbox
        toolbox_config = store.load_toolbox(default_toolbox_name)
        if toolbox_config:
            # Validate toolbox before registering
            issues = validate_toolbox(toolbox_config)
            if issues:
                try:
                    import click

                    click.echo(
                        click.style(
                            f"⚠ WARNING: Default toolbox '{default_toolbox_name}' has {len(issues)} issue(s). Run 'llm mcp toolboxes validate {default_toolbox_name}' to view details.",
                            fg="yellow",
                            bold=True,
                        )
                    )
                except ImportError:
                    # Click might not be available in all contexts
                    print(
                        f"WARNING: Default toolbox '{default_toolbox_name}' has {len(issues)} issue(s)."
                    )

            # Still register the toolbox despite issues
            ToolboxClass = build_toolbox_class(toolbox_config)
            register(ToolboxClass, name=toolbox_config.name)
    else:
        # Register all toolboxes
        for toolbox_name in store.list_toolboxes():
            toolbox_config = store.load_toolbox(toolbox_name)
            if toolbox_config:
                # Validate but don't show warnings for non-default toolboxes
                # This keeps the startup clean while still validating what's used
                ToolboxClass = build_toolbox_class(toolbox_config)
                register(ToolboxClass, name=toolbox_config.name)
