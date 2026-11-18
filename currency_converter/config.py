"""Application configuration from command-line arguments and environment variables."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_SOURCE_URL = "https://www.bnm.md/ru/official_exchange_rates"
DATA_DIR_ENV = "CURRENCY_CONVERTER_DATA_DIR"
CACHE_FILE_NAME = "rates-cache.json"


@dataclass(frozen=True)
class AppConfig:
    """Everything the composition root needs to build the application."""

    data_dir: Path
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    source_url: str = DEFAULT_SOURCE_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    open_browser: bool = True

    @property
    def cache_file(self) -> Path:
        return self.data_dir / CACHE_FILE_NAME


def default_data_dir(environ: Mapping[str, str]) -> Path:
    """User data directory: the env override, %APPDATA% on Windows, ~/.local/share elsewhere."""
    override = environ.get(DATA_DIR_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    appdata = environ.get("APPDATA", "").strip()
    if appdata:
        return Path(appdata) / "CurrencyConverter"
    return Path.home() / ".local" / "share" / "currency-converter"


def _port(text: str) -> int:
    value = int(text)
    if not 0 <= value <= 65535:
        raise argparse.ArgumentTypeError("port must be between 0 and 65535")
    return value


def _positive_float(text: str) -> float:
    value = float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Конвертер валют по официальным курсам Национального банка Молдовы.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="адрес сервера (по умолчанию 127.0.0.1)")
    parser.add_argument("--port", type=_port, default=DEFAULT_PORT, help="порт (по умолчанию 8765)")
    parser.add_argument("--data-dir", type=Path, help=f"папка для сохранённых курсов (или {DATA_DIR_ENV})")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help="адрес XML-ленты курсов НБМ")
    parser.add_argument(
        "--timeout", type=_positive_float, default=DEFAULT_TIMEOUT_SECONDS,
        help="таймаут запроса к НБМ в секундах (по умолчанию 8)",
    )
    parser.add_argument("--no-browser", action="store_true", help="не открывать окно браузера")
    return parser


def parse_config(
    argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None
) -> AppConfig:
    environ = os.environ if environ is None else environ
    args = build_parser().parse_args(argv)
    return AppConfig(
        data_dir=args.data_dir if args.data_dir else default_data_dir(environ),
        host=args.host,
        port=args.port,
        source_url=args.source_url,
        timeout=args.timeout,
        open_browser=not args.no_browser,
    )
