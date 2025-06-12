import logging
import os
from utils.helpers import load_config


def setup_logger(name: str, log_level=logging.INFO):
    config = load_config()

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    logs_dir = config['data']['reports']
    os.makedirs(logs_dir, exist_ok=True)

    formatter = logging.Formatter("[{levelname}] {asctime} {name}: {message}", style="{")


    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    log_file = os.path.join(logs_dir, f"{name}.log")
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

