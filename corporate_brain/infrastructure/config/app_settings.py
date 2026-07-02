"""User-facing app preferences persisted to a local JSON file (not env-driven)."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = Path("./app_settings.json")


@dataclass
class AppSettings:
    enable_source_selection: bool = False


def load_app_settings(path: Path = DEFAULT_SETTINGS_PATH) -> AppSettings:
    if not path.exists():
        return AppSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppSettings(**{**asdict(AppSettings()), **data})
    except (json.JSONDecodeError, TypeError) as error:
        logger.warning("Failed to read app settings from %s: %s", path, error)
        return AppSettings()


def save_app_settings(settings: AppSettings, path: Path = DEFAULT_SETTINGS_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
