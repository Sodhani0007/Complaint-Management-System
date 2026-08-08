"""
Structured logging setup. Called once from main.py at startup. Every AI call
(model used, latency, confidence) and every request-level error should flow
through this, since the log output is genuinely useful evidence in the demo
video ("here's the log showing the LangGraph run picking gemma2-9b-it and
returning 0.87 confidence").
"""

import logging
import sys


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Quiet down noisy third-party loggers so our own log lines aren't buried
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
