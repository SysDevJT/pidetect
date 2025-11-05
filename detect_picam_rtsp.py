#!/usr/bin/env python3
from vision_app.main import main_loop
import logging

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info("Shutting down")
    except Exception as e:
        logging.critical(f"Unhandled exception in main_loop: {e}", exc_info=True)
