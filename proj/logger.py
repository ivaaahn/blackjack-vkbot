import logging
from dataclasses import dataclass
from typing import Mapping


@dataclass
class LoggerConfig:
    base_level: str = "INFO"
    log_format: str = "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    stderr_logger: bool = True
    stderr_logger_level: str = "INFO"
    file_logger: bool = True
    file_logger_level: str = "WARNING"
    file_logger_filename: str = "logs.log"


class LoggerFactory:
    def __init__(self, conf: Mapping):
        self._raw_conf = conf
        self._conf = self._parse_config()

    def _parse_config(self) -> LoggerConfig:
        return LoggerConfig(**self._raw_conf)

    def _setup_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)

        logger.setLevel(self._conf.base_level)

        if self._conf.file_logger:
            self._add_file_handler(logger)

        if self._conf.stderr_logger:
            self._add_stderr_handler(logger)

        return logger

    def create(self, name: str) -> logging.Logger:
        new_logger = self._setup_logger(name)
        return new_logger

    def _add_file_handler(self, logger: logging.Logger):
        file_handler = logging.FileHandler(self._conf.file_logger_filename)
        file_handler.setLevel(self._conf.file_logger_level)
        file_handler.setFormatter(logging.Formatter(self._conf.log_format))

        logger.addHandler(file_handler)

    def _add_stderr_handler(self, logger: logging.Logger):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self._conf.stderr_logger_level)
        stream_handler.setFormatter(logging.Formatter(self._conf.log_format))

        logger.addHandler(stream_handler)
