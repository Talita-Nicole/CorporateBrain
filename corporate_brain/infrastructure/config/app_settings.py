"""User-facing app preferences persisted to a local JSON file (not env-driven)."""

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = Path("./app_settings.json")


@dataclass
class AppSettings:
    enable_source_selection: bool = False
    # Empty string means "use the BRAND_NAME/BRAND_LOGO_PATH env var default"
    # (see presentation/components/branding.py) — these two fields let the
    # user override that default from the Settings UI without editing .env.
    company_name: str = ""
    company_logo_path: str = ""


def load_app_settings(path: Path = DEFAULT_SETTINGS_PATH) -> AppSettings:
    if not path.exists():
        return AppSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Drop keys that no longer exist on AppSettings (e.g. a field removed
        # in a later version) instead of letting them fail construction —
        # an old settings file should degrade to defaults for the removed
        # field, not blow away every other saved preference.
        known_fields = {f.name for f in fields(AppSettings)}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return AppSettings(**{**asdict(AppSettings()), **filtered_data})
    except (json.JSONDecodeError, TypeError) as error:
        logger.warning("Failed to read app settings from %s: %s", path, error)
        return AppSettings()


def save_app_settings(settings: AppSettings, path: Path = DEFAULT_SETTINGS_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
