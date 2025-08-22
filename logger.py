import logging
import sys

class ColorizingStreamHandler(logging.StreamHandler):
    def __init__(self, stream=sys.stdout):
        super().__init__(stream)
        self._colors = {
            'DEBUG': '\033[94m',  # Blue
            'INFO': '',   # Default terminal color
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',  # Red
            'CRITICAL': '\033[91m',  # Red
        }
        self._reset = '\033[0m'

    def format(self, record):
        log_message = super().format(record)
        return f"{self._colors.get(record.levelname, '')}{log_message}{self._reset}"

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = ColorizingStreamHandler()
    formatter = logging.Formatter('[%(levelname)s] - %(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(logging.FileHandler('plex_rpc.log'))
    return logger
