import logging
import sys

def init_logging(
    level=logging.INFO,
    log_file=None,
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
) -> logging.Logger:
    """初始化 logging"""
    logger = logging.getLogger()
    logger.setLevel(level)

    # 清除已有的 Handler，避免重复输出
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 Handler（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

LOGGER = init_logging()