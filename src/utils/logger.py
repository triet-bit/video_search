import logging


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = False,
    filename: str = "app.log",
) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_to_file:
        handlers.append(logging.FileHandler(filename, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """Trả về logger theo tên module, dùng cho from utils.logger import get_logger."""
    return logging.getLogger(name)


log = logging.getLogger(__name__)