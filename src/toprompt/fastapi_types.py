from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FastApiAppLike(Protocol):
    """Protocol for in-memory database-like objects."""

    def openapi(self, *args, **kwargs) -> Any: ...


def format_fastapi_app(app: Any) -> str:
    """Generate human-readable documentation from FastAPI application."""
    schema = app.openapi()
    lines = ["FastAPI Application Schema:"]

    # Info section
    if info := schema.get("info", {}):
        if title := info.get("title"):
            lines.append(f"\nTitle: {title}")
        if description := info.get("description"):
            lines.append(f"Description: {description}")
        if version := info.get("version"):
            lines.append(f"Version: {version}")

    # Endpoints
    lines.append("\nEndpoints:")
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        lines.append(f"\n{path}")
        for method, details in methods.items():
            method_upper = method.upper()
            desc = details.get("description", "No description")
            lines.append(f"  {method_upper}: {desc}")

            # Parameters
            if params := details.get("parameters"):
                lines.append("  Parameters:")
                for param in params:
                    req = "*" if param.get("required") else ""
                    param_type = param.get("schema", {}).get("type", "any")
                    lines.append(
                        f"    - {param['name']}{req}: {param_type} "
                        f"({param.get('description', 'No description')})"
                    )

            # Request body
            if (body := details.get("requestBody")) and (
                ref := (
                    body.get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                    .get("$ref")
                )
            ):
                schema_name = ref.split("/")[-1]
                lines.append(f"  Request Body: {schema_name}")

            # Responses
            if responses := details.get("responses"):
                lines.append("  Responses:")
                for status, response in responses.items():
                    desc = response.get("description", "No description")
                    lines.append(f"    {status}: {desc}")
                    if ref := (
                        response.get("content", {})
                        .get("application/json", {})
                        .get("schema", {})
                        .get("$ref")
                    ):
                        schema_name = ref.split("/")[-1]
                        lines.append(f"      Schema: {schema_name}")

    return "\n".join(lines)
