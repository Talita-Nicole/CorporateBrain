"""Branding configuration: env vars as the default, overridable from Settings.

Precedence: a user-set value persisted in ``AppSettings`` (company name /
logo, set via the Settings modal) wins over the ``BRAND_NAME`` /
``BRAND_LOGO_PATH`` env vars, which remain the initial default for a fresh
install with no saved override.
"""

import base64
import os
from dataclasses import dataclass
from pathlib import Path

from infrastructure.config.app_settings import load_app_settings

_MIME_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@dataclass(frozen=True)
class BrandConfig:
    company_name: str
    primary_color: str
    logo_base64: str | None
    logo_mime_type: str | None
    logo_path: str | None


def load_brand_config() -> BrandConfig:
    settings = load_app_settings()

    company_name = settings.company_name.strip() or os.getenv("BRAND_NAME", "Knowledge Base")
    primary_color = os.getenv("BRAND_COLOR", "#6c63ff")
    logo_path = settings.company_logo_path.strip() or os.getenv("BRAND_LOGO_PATH", "")

    logo_base64 = None
    logo_mime_type = None
    resolved_logo_path = None
    if logo_path:
        path = Path(logo_path)
        if path.exists():
            logo_base64 = base64.b64encode(path.read_bytes()).decode()
            logo_mime_type = _MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")
            resolved_logo_path = str(path)

    return BrandConfig(
        company_name=company_name,
        primary_color=primary_color,
        logo_base64=logo_base64,
        logo_mime_type=logo_mime_type,
        logo_path=resolved_logo_path,
    )
