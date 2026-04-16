"""
Logging configuration for Echo Audio Converter.
"""

import logging
from pathlib import Path
from typing import List
from collections import deque


class LogBuffer(logging.Handler):
    def __init__(self, maxlen: int = 500):
        super().__init__()
        self.buffer: deque = deque(maxlen=maxlen)
    
    def emit(self, record):
        msg = self.format(record)
        self.buffer.append(msg)
    
    def get_logs(self) -> List[str]:
        return list(self.buffer)
    
    def clear(self):
        self.buffer.clear()


log_buffer = LogBuffer(maxlen=500)


def setup_logging(app_dir: Path) -> logging.Logger:
    logger = logging.getLogger("EchoAudioConverter")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    
    log_file = app_dir / "EAC_Log.txt"
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    log_buffer.setLevel(logging.INFO)
    log_buffer.setFormatter(formatter)
    logger.addHandler(log_buffer)
    
    logger.info(f"Logging initialized: {log_file}")
    
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("EchoAudioConverter")
