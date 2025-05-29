from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

# --------------------------------------------------------------------------- #
# 1.  Tool *source* models - one for every place a tool can live              #
# --------------------------------------------------------------------------- #


class MCPToolRef(BaseModel):
    """Reference to a tool that lives on an MCP server."""

    # Using json_schema_extra to ensure the discriminator is included
    kind: Literal["mcp"] = Field(
        "mcp", json_schema_extra={"discriminator": True}
    )

    server: str = Field(
        ...,
        description="Server name - the SAME string we already use in store/*.json",
        pattern="^[a-z0-9_]+$",
    )
    tool: str = Field(
        ...,
        description="Tool name as published by the server",
        pattern="^[A-Za-z0-9_-]+$",
    )

    # Optional overrides - identical on every subclass
    name: str | None = Field(None, description="Rename the tool")
    description: str | None = None

    # Backward compatibility properties
    @property
    def source_type(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return "mcp"

    @property
    def mcp_ref(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return f"{self.server}/{self.tool}"

    @property
    def function_name(self) -> None:
        """Backward compatibility with old ToolboxTool API."""
        return None

    @property
    def code(self) -> None:
        """Backward compatibility with old ToolboxTool API."""
        return None

    @property
    def tool_name(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return self.name or self.tool


class PythonToolRef(BaseModel):
    """Reference to a plain Python callable on the import-path."""

    # Using json_schema_extra to ensure the discriminator is included
    kind: Literal["python"] = Field(
        "python", json_schema_extra={"discriminator": True}
    )

    module: str = Field(
        ...,
        description="Import path, e.g. 'mypkg.mymodule'",
        pattern=r"^[A-Za-z_][A-Za-z0-9_.]*$",
    )
    attr: str = Field(
        ...,
        description="Name of the function / class / method inside the module",
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )

    name: str | None = None
    description: str | None = None

    # Backward compatibility properties
    @property
    def source_type(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return "function"

    @property
    def mcp_ref(self) -> None:
        """Backward compatibility with old ToolboxTool API."""
        return None

    @property
    def function_name(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return self.attr

    @property
    def code(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return f"# Auto-imported from {self.module}.{self.attr}"

    @property
    def tool_name(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return self.name or self.attr


class ToolboxMethodRef(BaseModel):
    """
    Reference to a *method* that lives **inside another toolbox class**.

    This is a special case of PythonToolRef where the module is a toolbox
    and the attr is a method inside that toolbox's class.
    """

    # Using json_schema_extra to ensure the discriminator is included
    kind: Literal["toolbox"] = Field(
        "toolbox", json_schema_extra={"discriminator": True}
    )

    toolbox: str = Field(
        ...,
        description="Name of the toolbox containing the method",
        pattern="^[a-z][a-z0-9_]*$",
    )
    method: str = Field(
        ...,
        description="Name of the method inside the toolbox",
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )

    name: str | None = None
    description: str | None = None

    # Backward compatibility properties
    @property
    def source_type(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return "toolbox_class"

    @property
    def mcp_ref(self) -> None:
        """Backward compatibility with old ToolboxTool API."""
        return None

    @property
    def function_name(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return self.method

    @property
    def code(self) -> None:
        """Backward compatibility with old ToolboxTool API."""
        return None

    @property
    def tool_name(self) -> str:
        """Backward compatibility with old ToolboxTool API."""
        return self.name or self.method


# --------------------------------------------------------------------------- #
# 2.  Discriminated union - the single list type we'll use everywhere         #
# --------------------------------------------------------------------------- #

ToolRef = Annotated[
    MCPToolRef | PythonToolRef | ToolboxMethodRef,
    Field(discriminator="kind"),
]


# --------------------------------------------------------------------------- #
# 3.  High-level toolbox definition                                           #
# --------------------------------------------------------------------------- #


class ToolboxConfig(BaseModel):
    """
    Persisted definition of a toolbox **before** it`s turned into live llm.Tools.
    Pure data, no behaviour.
    """

    name: str = Field(
        ...,
        description="Unique toolbox identifier",
        pattern="^[a-z][a-z0-9_]*$",
    )
    description: str | None = None
    tools: list[ToolRef] = Field(default_factory=list)

    # Arbitrary, toolbox-specific configuration blob (auth tokens, defaults, etc)
    config: dict = Field(default_factory=dict)

    # -------  tiny convenience helpers -----------
    @field_validator("tools")
    @classmethod
    def _no_duplicate_names(cls, v: list[ToolRef]) -> list[ToolRef]:
        """Fail fast if overrides create naming collisions *inside* one toolbox."""
        seen: set[str] = set()
        for ref in v:
            public_name = (
                ref.name
                or getattr(ref, "tool", None)
                or getattr(ref, "attr", None)
                or getattr(ref, "method", None)
            )
            if public_name is None:
                continue  # Skip if no valid name could be determined
            if public_name in seen:
                raise ValueError(
                    f"Duplicate tool name in toolbox: {public_name!r}"
                )
            seen.add(public_name)
        return v
