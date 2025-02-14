import logging


class LogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    white = "\x1b[37;0m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    datefmt = "%Y-%m-%d %H:%M:%S"
    base_style = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS: dict[int, str] = {
        logging.DEBUG: grey + base_style + reset,  # type: ignore
        logging.INFO: white + base_style + reset,  # type: ignore
        logging.WARNING: yellow + base_style + reset,  # type: ignore
        logging.ERROR: red + base_style + reset,  # type: ignore
        logging.CRITICAL: bold_red + base_style + reset,  # type: ignore
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(LogFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


LOGGER = get_logger(__name__)

logging.getLogger().setLevel(logging.WARNING)
LOGGER.setLevel(logging.INFO)
