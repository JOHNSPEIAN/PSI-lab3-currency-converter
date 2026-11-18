"""Composition root: the only module that knows concrete classes and wires them together."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Sequence

from currency_converter import __version__
from currency_converter.adapters.bnm import BnmRateProvider, BnmXmlParser
from currency_converter.adapters.browser import (
    AppWindowLauncher, DefaultBrowserLauncher, FallbackBrowserLauncher,
)
from currency_converter.adapters.clock import SystemClock
from currency_converter.adapters.http_client import UrllibHttpClient
from currency_converter.adapters.json_cache import JsonFileRateCache
from currency_converter.adapters.memo import MemoizingRateProvider
from currency_converter.application.converter_service import ConverterService
from currency_converter.application.rate_service import RateService
from currency_converter.config import AppConfig, parse_config
from currency_converter.domain.conversion import CurrencyConverter
from currency_converter.domain.validation import ConversionRequestValidator
from currency_converter.presentation.json_presenter import JsonPresenter
from currency_converter.web.api import ApiController
from currency_converter.web.responses import ApiHandler
from currency_converter.web.server import bind_server

log = logging.getLogger("currency_converter")


@dataclass(frozen=True)
class Application:
    config: AppConfig
    api: ApiHandler


def build_application(config: AppConfig) -> Application:
    clock = SystemClock()
    http = UrllibHttpClient(timeout=config.timeout, user_agent=f"CurrencyConverter/{__version__}")
    bnm = BnmRateProvider(http, BnmXmlParser(), base_url=config.source_url)
    provider = MemoizingRateProvider(bnm, clock)
    rate_service = RateService(provider, JsonFileRateCache(config.cache_file), clock)
    service = ConverterService(rate_service, CurrencyConverter(), ConversionRequestValidator(), clock)
    api = ApiController(service, JsonPresenter(), version=__version__)
    return Application(config=config, api=api)


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
    if config.open_browser:
        launcher = FallbackBrowserLauncher([AppWindowLauncher(), DefaultBrowserLauncher()])
        if not launcher.open(url):
            print("Откройте адрес в браузере вручную.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        server.server_close()
    return 0
