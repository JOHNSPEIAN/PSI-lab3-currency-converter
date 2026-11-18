"""HTTP client adapter on urllib; every transport problem becomes SourceUnavailableError."""

from __future__ import annotations

import http.client
import urllib.error
import urllib.request

from currency_converter.domain.errors import (
    HttpStatusError, MalformedResponseError, SourceUnavailableError,
)

MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class UrllibHttpClient:
    def __init__(self, timeout: float, user_agent: str) -> None:
        self._timeout = timeout
        self._user_agent = user_agent

    def get(self, url: str) -> bytes:
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": self._user_agent,
                "Accept": "application/xml, text/xml;q=0.9, */*;q=0.1",
            })
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:  # subclass of URLError: must come first
            raise HttpStatusError(exc.code) from exc
        except urllib.error.URLError as exc:
            raise SourceUnavailableError(str(exc.reason)) from exc
        except (TimeoutError, ConnectionError, http.client.HTTPException, OSError) as exc:
            raise SourceUnavailableError(type(exc).__name__) from exc
        except ValueError as exc:  # malformed URL, e.g. a wrong --source-url
            raise SourceUnavailableError(f"bad URL: {exc}") from exc
        if len(payload) > MAX_RESPONSE_BYTES:
            raise MalformedResponseError("response is too large")
        return payload
