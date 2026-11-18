"""Composition root: the only module that knows concrete classes and wires them together."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Sequence

from currency_converter import __version__
from currency_converter.config import AppConfig, parse_config
from currency_converter.web.responses import ApiHandler, ApiRequest, ApiResponse, error_body
from currency_converter.web.server import bind_server

log = logging.getLogger("currency_converter")


class _NotImplementedApi:
    """Placeholder until the API controller exists (Phase 2 checkpoint)."""

    def handle(self, request: ApiRequest) -> ApiResponse:
        return ApiResponse(404, error_body("NOT_FOUND", "Не найдено."))


@dataclass(frozen=True)
class Application:
    config: AppConfig
    api: ApiHandler


def build_application(config: AppConfig) -> Application:
    return Application(config=config, api=_NotImplementedApi())


def _configure_console() -> None:
    """Windows consoles often use cp1252; Russian text must never crash logging (research R9)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _configure_console()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = parse_config(argv)
    app = build_application(config)
    server = bind_server(config.host, config.port, app.api)
    url = f"http://{config.host}:{server.server_port}/"
    print(f"Конвертер валют {__version__} запущен: {url}")
    print(f"Сохранённые курсы: {config.cache_file}")
    print("Для остановки нажмите Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        server.server_close()
    return 0
