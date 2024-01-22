import logging
from datetime import datetime
from settings import DEBUG, LOG_DIRECTORY_PATH


_LOG_FORMAT = "%(asctime)s %(levelname)s - %(funcName)s: %(message)s"


def _create_file_handler() -> logging.FileHandler:
    current_time_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    handler = logging.FileHandler(
        filename=LOG_DIRECTORY_PATH / f"caa_forms_{current_time_string}.log"
    )
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT))
    return handler


logging.basicConfig(
    format=_LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("caa_forms")
logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)
logger.addHandler(_create_file_handler())
