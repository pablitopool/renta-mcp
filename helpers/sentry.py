import os

try:
    import sentry_sdk
except ModuleNotFoundError:  # pragma: no cover - fallback de entorno
    sentry_sdk = None


def init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn or sentry_sdk is None:
        return

    sample_rate = float(os.getenv("SENTRY_SAMPLE_RATE", "1.0"))
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("MCP_ENV", "local"),
        traces_sample_rate=sample_rate,
        profiles_sample_rate=sample_rate,
        send_default_pii=False,
    )
