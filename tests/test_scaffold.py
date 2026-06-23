from royale_analytics import __version__
from royale_analytics.errors import (
    AccessDeniedError,
    ApiError,
    RoyaleAnalyticsError,
)


def test_version_is_pinned():
    assert __version__ == "0.1.0"


def test_api_error_carries_status_and_guidance():
    err = ApiError("x", status=403, guidance="g")
    assert err.status == 403
    assert err.guidance == "g"
    assert str(err) == "x"


def test_api_error_defaults():
    err = ApiError("boom")
    assert err.status is None
    assert err.guidance == ""


def test_access_denied_is_api_error_and_base_error():
    assert issubclass(AccessDeniedError, ApiError)
    assert issubclass(AccessDeniedError, RoyaleAnalyticsError)
