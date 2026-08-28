"""Public Mindgarden 0.x library surface."""

from .adapters.publishing import project_garden, verify_projection
from .application.agent import (
    build_index,
    render_context_json,
    render_context_markdown,
    render_llms_txt,
    search_payload,
)
from .domain.validation import ContractError, validate_repository

__version__ = "0.1.0"

__all__ = [
    "ContractError",
    "__version__",
    "build_index",
    "project_garden",
    "render_context_json",
    "render_context_markdown",
    "render_llms_txt",
    "search_payload",
    "validate_repository",
    "verify_projection",
]
