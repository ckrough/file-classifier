import logging
import logging.config
import sys


def setup_logging():
    """
    Configures logging for the entire application.
    """
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'stream': sys.stdout,
            }
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'loggers': {
            'file-analyzer': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False
            },
        }
    }

    logging.config.dictConfig(logging_config)
