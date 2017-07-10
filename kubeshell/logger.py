import os
import sys
import logging
import traceback
import logging.config

if not os.path.exists(os.path.expanduser("~/.kube/shell")):
    try:
        os.makedirs(os.path.expanduser("~/.kube/shell"))
    except OSError:
        print("failed to make config dirs for kube-shell")
        traceback.print_exc(file=sys.stdout)

logfile = os.path.expanduser("~/.kube/shell/error.log")
loggingConf = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)-15s [%(levelname)-4s] %(name)s %(funcName)s:%(lineno)s - %(message)s",
        }
    },
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
            "level": "ERROR"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": logfile,
            "backupCount": 3,
            "maxBytes": 10485760  # 10MB
        }
    },
    "loggers": {
        "": {
            "level": "ERROR",
            "handlers": ["file"],
        },
        "urllib3": {
            "level": "ERROR",
            "handlers": ["file"],
            "propagate": False
        },
        "kubeshell": {
            "level": "INFO",
            "handlers": ["file"],
            "propagate": False
        }
    },
}
logging.config.dictConfig(loggingConf)