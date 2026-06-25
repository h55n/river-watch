"""
gee_auth.py — Google Earth Engine authentication / initialization helper.

Earth Engine is free for non-commercial and research use but requires a one-time
account registration + auth flow. This module centralizes init so every other
pipeline script just does:

    from pipeline.gee_auth import init_ee
    init_ee()

Two auth paths are supported:
1. Interactive (local dev): run `earthengine authenticate` once in your shell,
   then init_ee() will pick up the cached credentials.
2. Service account (CI / Streamlit Cloud): set the GOOGLE_APPLICATION_CREDENTIALS
   env var to point at a service account JSON key, and set EE_SERVICE_ACCOUNT to
   the service account email.
"""

from __future__ import annotations

import os
import sys

try:
    import ee
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "earthengine-api is not installed. Run: pip install earthengine-api"
    ) from exc

_INITIALIZED = False


class EarthEngineAuthError(RuntimeError):
    """Raised when Earth Engine cannot be initialized with available credentials."""


def init_ee(project: str | None = None, force: bool = False) -> None:
    """
    Initialize the Earth Engine API. Safe to call multiple times — only the
    first call (or a call with force=True) actually hits the network.

    Args:
        project: GCP project ID registered for Earth Engine. If None, falls back
            to the EE_PROJECT env var, then to ee's own default resolution.
        force: re-run initialization even if already initialized this process.
    """
    global _INITIALIZED
    if _INITIALIZED and not force:
        return

    project = project or os.environ.get("EE_PROJECT")
    service_account = os.environ.get("EE_SERVICE_ACCOUNT")
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    try:
        if service_account and key_path:
            credentials = ee.ServiceAccountCredentials(service_account, key_path)
            ee.Initialize(credentials, project=project)
        else:
            # Interactive / cached-credentials path. Will raise if the user has
            # never run `earthengine authenticate`.
            ee.Initialize(project=project)
    except Exception as exc:  # noqa: BLE001 - we want to wrap *any* ee init failure
        raise EarthEngineAuthError(
            "Could not initialize Earth Engine.\n"
            "  - For local dev: run `earthengine authenticate` once, then retry.\n"
            "  - For service-account / hosted use: set GOOGLE_APPLICATION_CREDENTIALS "
            "to a service account JSON key path and EE_SERVICE_ACCOUNT to its email.\n"
            f"Underlying error: {exc}"
        ) from exc

    _INITIALIZED = True


def is_initialized() -> bool:
    return _INITIALIZED


if __name__ == "__main__":
    # Quick CLI smoke test: `python -m pipeline.gee_auth`
    try:
        init_ee()
        print("Earth Engine initialized OK.")
        sys.exit(0)
    except EarthEngineAuthError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
