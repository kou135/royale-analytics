from __future__ import annotations

import time
from typing import Any, Callable

import httpx

from royale_analytics.errors import (
    AccessDeniedError,
    ApiError,
    ApiServerError,
    MaintenanceError,
    NotFoundError,
    ThrottledError,
)
from royale_analytics.tags import encode_tag

_ACCESS_DENIED_GUIDANCE = (
    "Access denied (403). Your token is invalid or the request IP is not "
    "whitelisted. When using the RoyaleAPI proxy, whitelist the IP "
    "45.79.218.79 on developer.clashroyale.com; for a direct connection, "
    "re-issue the key with your current IP."
)
_NOT_FOUND_GUIDANCE = (
    "Not found (404). Check the player tag (the letter 'O' must be the digit "
    "'0', and the '#' is not part of the tag)."
)
_MAINTENANCE_GUIDANCE = (
    "Service in maintenance (503). Supercell is performing maintenance; "
    "retry later."
)
_THROTTLED_GUIDANCE = (
    "Throttled (429). The rate limit was exceeded and retries were exhausted; "
    "wait and try again."
)
_SERVER_ERROR_GUIDANCE = (
    "Server error from the API. This is usually transient; retry later."
)


class ApiClient:
    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        client: "httpx.Client | None" = None,
        max_retries: int = 2,
        sleep: "Callable[[float], None]" = time.sleep,
    ) -> None:
        self.token = token
        self.base_url = base_url
        self.client = client if client is not None else httpx.Client(base_url=base_url)
        self.max_retries = max_retries
        self.sleep = sleep

    def _get(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"}
        attempts = 0
        while True:
            response = self.client.get(path, headers=headers)
            status = response.status_code

            if 200 <= status < 300:
                return response.json()

            if status == 429:
                retry_after_us = response.headers.get("x-ratelimit-retry-after")
                seconds = float(retry_after_us) / 1_000_000 if retry_after_us else 0.0
                if attempts < self.max_retries:
                    attempts += 1
                    self.sleep(seconds)
                    continue
                raise ThrottledError(
                    "Throttled after retries.",
                    status=429,
                    guidance=_THROTTLED_GUIDANCE,
                )

            if status == 403:
                raise AccessDeniedError(
                    "Access denied.", status=403, guidance=_ACCESS_DENIED_GUIDANCE
                )
            if status == 404:
                raise NotFoundError(
                    "Not found.", status=404, guidance=_NOT_FOUND_GUIDANCE
                )
            if status == 503:
                raise MaintenanceError(
                    "In maintenance.", status=503, guidance=_MAINTENANCE_GUIDANCE
                )
            if 500 <= status < 600:
                raise ApiServerError(
                    f"Server error ({status}).",
                    status=status,
                    guidance=_SERVER_ERROR_GUIDANCE,
                )
            raise ApiError(
                f"Unexpected API response ({status}).",
                status=status,
                guidance="Unexpected response from the API.",
            )
