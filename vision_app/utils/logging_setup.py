import logging
import sys
from ..config import Config

def setup_logging():
    """Configures the root logger."""
    level = logging.getLevelName(Config.LOG_LEVEL)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Console handler
    _console = logging.StreamHandler(sys.stdout)
    _console.setLevel(level)
    _console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))

    # Remove existing handlers and add the new one
    logger.handlers = [_console]

    # Silence excessively verbose loggers
    logging.getLogger("ultralytics").setLevel(logging.ERROR)
    logging.getLogger("picamera2").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Add a filter to suppress specific messages if needed
    class SuppressFilter(logging.Filter):
        def filter(self, record):
            # Example: return not record.getMessage().startswith("Suppressed message")
            return True

    logger.addFilter(SuppressFilter())
