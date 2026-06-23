"""Streamlit entrypoint: load configuration, set up logging and run the app."""

import logging
import os

from dotenv import load_dotenv

DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def _configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO), format=LOG_FORMAT
    )


def main() -> None:
    load_dotenv()
    _configure_logging()
    from presentation.app import run

    run()


if __name__ == "__main__":
    main()
