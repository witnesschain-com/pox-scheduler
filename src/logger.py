import logging
import os

class Logger:
    _instance = None
    _logger = None

    def __new__(cls, log_path: str = "./", log_name: str = "pox_schedule.log"):
        # Singleton pattern to ensure only one logger instance
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._setup_logger(log_path, log_name)
        return cls._instance

    @classmethod
    def _setup_logger(cls, log_path: str, log_name: str) -> None:
        """Set up the logger with specified configuration"""
        cls._logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            filename=os.path.join(log_path, log_name),
            filemode='a',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    @classmethod
    def info(cls, message: str) -> None:
        """Log info level message"""
        if cls._logger is None:
            cls._setup_logger("./", "pox_schedule.log")
        cls._logger.info(message)

    @classmethod
    def error(cls, message: str) -> None:
        """Log error level message"""
        if cls._logger is None:
            cls._setup_logger("./", "pox_schedule.log")
        cls._logger.error(message)

    @classmethod
    def warning(cls, message: str) -> None:
        """Log warning level message"""
        if cls._logger is None:
            cls._setup_logger("./", "pox_schedule.log")
        cls._logger.warning(message)

    @classmethod
    def debug(cls, message: str) -> None:
        """Log debug level message"""
        if cls._logger is None:
            cls._setup_logger("./", "pox_schedule.log")
        cls._logger.debug(message)