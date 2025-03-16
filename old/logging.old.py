import json
import logging
import logging.config

from fastapi import FastAPI

from app.config import Config


def configure_logging(app: FastAPI):
    """Configures structured logging for the FastAPI application using JSON format and request IDs."""
    config = Config()
    log_level = config.LOG_LEVEL.upper()  # Ensure uppercase for logging levels

    # --- JSON Logging Formatter ---
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "loggerName": record.name,
                "fileName": record.filename,
                "lineNumber": record.lineno,
                "functionName": record.funcName,
                "message": record.getMessage(),
                "requestId": record.__dict__.get("request_id", None),  # Get request ID from record if available
            }
            return json.dumps(log_record)

    # --- Handlers ---
    handlers = ["console"]  # Default to console handler

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "jsonFormatter": {
                "()": JsonFormatter,
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 format
            },
            "standardFormatter": {  # Fallback formatter if JSON fails or for non-JSON handlers
                "format": "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "jsonFormatter" if config.LOG_FORMAT.lower() == "json" else "standardFormatter",
                # Use JSON formatter based on config
                "stream": "ext://sys.stdout",  # or sys.stderr
            },
            # Example File Handler (optional, configure in LOG_HANDLERS)
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "jsonFormatter" if config.LOG_FORMAT.lower() == "json" else "standardFormatter",
                "filename": config.LOG_FILE_PATH,
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
            },
            # Example Syslog Handler (optional, configure in LOG_HANDLERS for external logging)
            # "syslog": {
            #     "class": "logging.handlers.SysLogHandler",
            #     "level": log_level,
            #     "formatter": "jsonFormatter" if config.LOG_FORMAT.lower() == "json" else "standardFormatter",
            #     "address": ('logs.example.com', 514), # Replace with your syslog server
            #     "facility": logging.handlers.SysLogHandler.LOG_USER,
            # },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": handlers,  # Handlers are dynamically set based on config
                "level": log_level,
                "propagate": True,
            },
            "uvicorn.access": {  # Disable uvicorn access logs in JSON format if not desired
                "handlers": ["console"],  # Or configure a separate handler for access logs
                "level": "INFO",  # Or config.UVICORN_ACCESS_LOG_LEVEL
                "propagate": False,  # Do not propagate to root logger to avoid duplicate logs
            },
            "sqlalchemy.engine": {  # Example: Configure SQLAlchemy engine logging if needed
                "handlers": ["console"],
                "level": "WARNING",  # Or config.SQLALCHEMY_LOG_LEVEL
                "propagate": False,
            },
            # Add more specific logger configurations here if needed
        },
    }

    # --- Dynamic Handler Configuration based on LOG_HANDLERS ---
    configured_handlers = config.LOG_HANDLERS.lower().split(',')  # e.g., "console,file"
    effective_handlers = []
    for handler_name in configured_handlers:
        handler_name = handler_name.strip()  # Remove whitespace
        if handler_name in log_config["handlers"]:
            effective_handlers.append(handler_name)
        elif handler_name:  # Only warn for non-empty strings
            logger = logging.getLogger(__name__)  # Get logger to log the warning
            logger.warning(
                f"Configured log handler '{handler_name}' is not defined in logging configuration. Available handlers are: {', '.join(log_config['handlers'].keys())}")

    log_config["loggers"][""]["handlers"] = effective_handlers  # Update root logger handlers

    # --- Apply Configuration ---
    logging.config.dictConfig(log_config)

    logger = logging.getLogger(__name__)  # Get the logger again after configuration to ensure it's correctly configured
    app.logger = logger  # Attach logger to FastAPI app instance (optional)
    logger.info(
        f"Logging configured with level: {log_level}, format: {config.LOG_FORMAT.upper()}, handlers: {', '.join(effective_handlers)}")  # Log configuration details
    return logger  # Return the configured logger instance
