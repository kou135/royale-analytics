"""Exception hierarchy shared by all royale_analytics modules."""

from __future__ import annotations


class RoyaleAnalyticsError(Exception):
    """Base class for all royale_analytics errors."""


class InvalidTagError(RoyaleAnalyticsError, ValueError):
    """Raised when a player tag fails normalization/validation."""


class BattleTimeParseError(RoyaleAnalyticsError, ValueError):
    """Raised when a battleTime string cannot be parsed."""


class ConfigError(RoyaleAnalyticsError):
    """Raised when required configuration is missing or invalid."""


class ApiError(RoyaleAnalyticsError):
    """Base class for HTTP/API errors.

    Carries the HTTP ``status`` (when known) and actionable ``guidance``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        guidance: str = "",
    ) -> None:
        super().__init__(message)
        self.status = status
        self.guidance = guidance


class AccessDeniedError(ApiError):
    """HTTP 403: invalid token or IP not whitelisted."""


class NotFoundError(ApiError):
    """HTTP 404: player tag not found."""


class ThrottledError(ApiError):
    """HTTP 429: rate limited (even after retries)."""


class MaintenanceError(ApiError):
    """HTTP 503: Supercell maintenance."""


class ApiServerError(ApiError):
    """HTTP 5xx: upstream server error."""
