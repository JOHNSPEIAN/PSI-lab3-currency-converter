"""Local HTTP server: serves the static UI and forwards /api/* to an injected ApiHandler."""

from __future__ import annotations

import json
import logging
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, unquote, urlsplit

from currency_converter.web.responses import ApiHandler, ApiRequest, ApiResponse, error_body

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 16 * 1024

# Explicit map: on Windows ``mimetypes`` reads the registry and may serve .js as text/plain,
# which browsers refuse to execute as an ES module.
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
    ".woff2": "font/woff2",
}

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

INTERNAL_ERROR_MESSAGE = "Внутренняя ошибка приложения. Подробности записаны в журнал."


class ConverterHttpServer(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR lets a second process bind an occupied port; we need the
    # bind to fail so that the next free port is chosen instead.
    allow_reuse_address = sys.platform != "win32"


class RequestHandler(BaseHTTPRequestHandler):
    """Routing only; all decisions about rates live behind ``api``."""

    api: ApiHandler
    static_dir: Path = STATIC_DIR
    server_version = "CurrencyConverter/1.0"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        self._dispatch()

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch(head=True)

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        log.debug("%s - %s", self.address_string(), format % args)

    def _dispatch(self, head: bool = False) -> None:
        try:
            url = urlsplit(self.path)
            if url.path.startswith("/api/"):
                self._handle_api(url.path, url.query)
            elif self.command in ("GET", "HEAD"):
                self._serve_static(url.path, head)
            else:
                self._send_json(ApiResponse(HTTPStatus.METHOD_NOT_ALLOWED, error_body(
                    "METHOD_NOT_ALLOWED", "Метод не поддерживается.")))
        except Exception:  # last line of defence: never let a request kill the app
            log.exception("unhandled error while serving %s %s", self.command, self.path)
            self._send_json(ApiResponse(HTTPStatus.INTERNAL_SERVER_ERROR,
                                        error_body("INTERNAL", INTERNAL_ERROR_MESSAGE)))

    def _handle_api(self, path: str, query: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json(ApiResponse(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, error_body(
                "BAD_REQUEST", "Слишком большой запрос.")))
            return
        body = self.rfile.read(length) if length else b""
        request = ApiRequest(
            method=self.command, path=path,
            query=dict(parse_qsl(query, keep_blank_values=True)), body=body,
        )
        self._send_json(self.api.handle(request))

    def _serve_static(self, path: str, head: bool) -> None:
        file = self._resolve_static(path)
        if file is None:
            self._send_json(ApiResponse(HTTPStatus.NOT_FOUND, error_body("NOT_FOUND", "Не найдено.")))
            return
        content = file.read_bytes()
        mime = MIME_TYPES.get(file.suffix.lower(), "application/octet-stream")
        self._send(HTTPStatus.OK, content, mime, [("Cache-Control", "no-cache")], head)

    def _resolve_static(self, path: str) -> Path | None:
        if path in ("/", "/index.html"):
            relative = "index.html"
        elif path == "/favicon.ico":
            relative = "img/logo.svg"
        elif path.startswith("/static/"):
            relative = unquote(path[len("/static/"):])
        else:
            return None
        root = self.static_dir.resolve()
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            return None
        return candidate

    def _send_json(self, response: ApiResponse) -> None:
        payload = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
        self._send(response.status, payload, "application/json; charset=utf-8",
                   [("Cache-Control", "no-store")])

    def _send(self, status: int, payload: bytes, mime: str,
              extra_headers: Iterable[tuple[str, str]] = (), head: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in (*SECURITY_HEADERS.items(), *extra_headers):
            self.send_header(name, value)
        self.end_headers()
        if not head:
            self.wfile.write(payload)


def make_handler(api: ApiHandler, static_dir: Path = STATIC_DIR) -> type[RequestHandler]:
    """A handler class bound to its dependencies (the stdlib server instantiates it per request)."""
    return type("BoundRequestHandler", (RequestHandler,), {"api": api, "static_dir": static_dir})


def bind_server(host: str, port: int, api: ApiHandler, attempts: int = 20) -> ConverterHttpServer:
    """Bind to ``port`` or the next free one (research R10); finally let the OS choose."""
    handler = make_handler(api)
    candidates = [port + i for i in range(attempts)] if port else []
    for candidate in [*candidates, 0]:
        try:
            return ConverterHttpServer((host, candidate), handler)
        except OSError as exc:
            log.info("port %s is busy (%s), trying the next one", candidate, exc)
    raise OSError("no free port")  # pragma: no cover - port 0 always succeeds in practice
