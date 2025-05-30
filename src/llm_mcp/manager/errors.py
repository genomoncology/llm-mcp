class ManagerError(Exception):
    """Base class for manager-level errors."""


class ToolboxExists(ManagerError):
    """Raised when attempting to create a toolbox that already exists."""


class ToolboxNotFound(ManagerError):
    """Raised when a requested toolbox does not exist."""


class ToolExists(ManagerError):
    """Raised when attempting to add a tool that already exists in a toolbox."""


class ToolNotFound(ManagerError):
    """Raised when a requested tool does not exist in a toolbox."""


class DefaultToolboxNotSet(ManagerError):
    """Raised when attempting to get the default toolbox when none is set."""


# ─── server-related ─────────────────────────────────────────────
class DuplicateServer(ManagerError):
    """Raised when attempting to create a server that already exists."""


class ServerNotFound(ManagerError):
    """Raised when a requested server does not exist."""
