import os

if not os.path.exists(os.path.expanduser("~/.kube-shell")):
    try:
        os.makedirs(os.path.expanduser("~/.kube-shell"))
    except OSError:
        pass

logfile = os.path.expanduser("~/.kube-shell/debug.log")
loggingConf = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %[levelname]-8s %(funcName)s:%(lineno)s - %(message)s",
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "level": "ERROR",
            "formatter": "default",
            "filename": logfile,
        }
    },
    "loggers": {
        "kubeshell": {
            "level": "ERROR",
            "handlers": ["file"],
            "propagate": "no",
        },
        "": {
            "level": "ERROR",
            "handlers": ["file"]
        }
    },
}
