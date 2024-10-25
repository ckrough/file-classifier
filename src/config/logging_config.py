import logging
import logging.config
import os


def setup_logging():
    # Get the DEBUG_MODE value from environment variables
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    # Set the logging level based on DEBUG_MODE
    log_level = logging.DEBUG if debug_mode else logging.INFO

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'level': logging.DEBUG,
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': 'app.log',
                'mode': 'a',
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default', 'file'],
                'level': log_level,
                'propagate': True
            },
        }
    }

    logging.config.dictConfig(logging_config)
