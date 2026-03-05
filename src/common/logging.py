from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logging with a simple, readable format.

    This is intentionally minimal and beginner-friendly.
    """
    if logging.getLogger().handlers:
        # Already configured
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger, ensuring logging is configured at least once.
    """
    if not logging.getLogger().handlers:
        setup_logging()
    return logging.getLogger(name if name is not None else __name__)

