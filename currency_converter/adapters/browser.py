"""Browser launchers: a desktop-like app window when possible, the default browser otherwise."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from currency_converter.ports import BrowserLauncher

log = logging.getLogger(__name__)

WINDOW_SIZE = "560,900"


def default_browser_candidates(environ: Mapping[str, str] | None = None) -> list[Path]:
    """Chromium-based browsers that support ``--app`` (Edge ships with Windows 10/11)."""
    environ = os.environ if environ is None else environ
    found: list[Path] = []
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        path = shutil.which(name)
        if path:
            found.append(Path(path))
    roots = [environ.get(key) for key in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    suffixes = ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe")
    found.extend(Path(root) / suffix for root in roots if root for suffix in suffixes)
    return found


class AppWindowLauncher:
    """Opens the UI in a chromeless window: ``msedge --app=<url>``."""

    def __init__(self, candidates: Iterable[Path] | None = None) -> None:
        self._candidates = list(candidates) if candidates is not None else default_browser_candidates()

    def open(self, url: str) -> bool:
        executable = next((p for p in self._candidates if p.is_file()), None)
        if executable is None:
            return False
        try:
            subprocess.Popen(  # noqa: S603 - fixed executable, our own localhost URL
                [str(executable), f"--app={url}", f"--window-size={WINDOW_SIZE}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
            )
        except OSError as exc:
            log.info("could not start %s: %s", executable, exc)
            return False
        return True


class DefaultBrowserLauncher:
    def open(self, url: str) -> bool:
        try:
            return webbrowser.open(url, new=1)
        except webbrowser.Error as exc:
            log.info("default browser failed: %s", exc)
            return False


class FallbackBrowserLauncher:
    """Tries launchers in order until one succeeds (Composite, open for new strategies)."""

    def __init__(self, launchers: Sequence[BrowserLauncher]) -> None:
        self._launchers = tuple(launchers)

    def open(self, url: str) -> bool:
        return any(launcher.open(url) for launcher in self._launchers)
