import argparse
import logging


def get_args():
    parser = argparse.ArgumentParser(
        description="Asynchronous microservice for downloading files"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="./test_photos",
        help="Path to main file storage",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        nargs="?",
        default=0,
        help="Imitates low connection speed",
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        nargs="?",
        choices=["debug", "info", "warning", "error", "critical"],
        default=None,
        help="Turns on logging and sets its level if provided",
    )
    return parser.parse_args()


def get_logger(level):
    if level:
        format = "%(asctime)s  %(levelname)s  %(message)s"
        logging.basicConfig(format=format, filename="app.log")
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, level.upper()))
        return logger
