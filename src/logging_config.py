import os
import sys
import logging
import logging.config


def setup_logging():
    """
    Sets up the logging configuration for the application.

    The configuration includes:
    - Console output with detailed formatting.
    - Log level controlled by the LOG_LEVEL environment variable.

    The default log level is DEBUG if not specified.
    """
    log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s in %(filename)s, function %(funcName)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed',
                'stream': sys.stdout,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': log_level,
        },
    }

    # Apply the logging configuration
    logging.config.dictConfig(logging_config)

    # Return a logger object for this module
    return logging.getLogger(__name__)
