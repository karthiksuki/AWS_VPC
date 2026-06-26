"""
vpc_manager/utils/logger.py — Structured logger with Rich console output.
"""
import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)