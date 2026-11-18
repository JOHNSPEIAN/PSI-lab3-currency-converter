"""JSON API controller: parses requests, calls the use case, delegates output to the presenter."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Any, Callable

from currency_converter.application.converter_service import ConverterService
from currency_converter.domain.errors import ConverterError
from currency_converter.presentation import messages_ru as ru
from currency_converter.presentation.json_presenter import JsonPresenter
from currency_converter.web.responses import ApiRequest, ApiResponse

log = logging.getLogger(__name__)


class BadRequest(Exception):
    pass


class ApiController:
    def __init__(self, service: ConverterService, presenter: JsonPresenter, version: str) -> None:
        self._service = service
        self._presenter = presenter
        self._version = version
        self._routes: dict[tuple[str, str], Callable[[ApiRequest], ApiResponse]] = {
            ("GET", "/api/health"): self._health,
            ("GET", "/api/rates"): self._rates,
            ("POST", "/api/convert"): self._convert,
        }

    def handle(self, request: ApiRequest) -> ApiResponse:
        route = self._routes.get((request.method, request.path))
        if route is None:
            return ApiResponse(HTTPStatus.NOT_FOUND, self._presenter.error("NOT_FOUND", ru.NOT_FOUND))
        try:
            return route(request)
        except BadRequest as exc:
            log.info("bad request %s: %s", request.path, exc)
            return ApiResponse(HTTPStatus.BAD_REQUEST, self._presenter.error("BAD_REQUEST", ru.BAD_REQUEST))
        except ConverterError as exc:
            log.info("%s: %s", type(exc).__name__, exc)
            status, body = self._presenter.present_error(exc)
            return ApiResponse(status, body)
        except Exception:
            log.exception("unexpected error in %s", request.path)
            return ApiResponse(HTTPStatus.INTERNAL_SERVER_ERROR, self._presenter.error("INTERNAL", ru.INTERNAL))

    def _health(self, request: ApiRequest) -> ApiResponse:
        return ApiResponse(HTTPStatus.OK, {"status": "ok", "version": self._version})

    def _rates(self, request: ApiRequest) -> ApiResponse:
        lookup = self._service.rates(request.query.get("date") or None)
        return ApiResponse(HTTPStatus.OK, self._presenter.present_rates(lookup))

    def _convert(self, request: ApiRequest) -> ApiResponse:
        data = self._json_body(request)
        outcome = self._service.convert(
            amount=self._text(data, "amount"), source=self._text(data, "source"),
            target=self._text(data, "target"), rate_date=self._text(data, "date"),
        )
        return ApiResponse(HTTPStatus.OK, self._presenter.present_conversion(outcome))

    @staticmethod
    def _json_body(request: ApiRequest) -> dict[str, Any]:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BadRequest(f"invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise BadRequest("JSON object expected")
        return data

    @staticmethod
    def _text(data: dict[str, Any], key: str) -> str | None:
        value = data.get(key)
        if value is None:
            return None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        if not isinstance(value, str):
            raise BadRequest(f"{key} must be a string")
        return value
