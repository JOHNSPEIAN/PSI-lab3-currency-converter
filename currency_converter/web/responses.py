"""Transport-neutral request/response types shared by the server and the API controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ApiRequest:
    method: str
    path: str
    query: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: Mapping[str, Any]


class ApiHandler(Protocol):
    def handle(self, request: ApiRequest) -> ApiResponse: ...


def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"status": "error", "error": {"code": code, "message": message, **extra}}
