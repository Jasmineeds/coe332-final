# src/logger_config.py
import os
import logging
import socket

# Read LOG_LEVEL from environment
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Setup log format
format_str = f'[%(asctime)s {socket.gethostname()}] %(filename)s:%(funcName)s:%(lineno)d - %(levelname)s: %(message)s'
logging.basicConfig(level=log_level, format=format_str)

# Provide logger getter
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
