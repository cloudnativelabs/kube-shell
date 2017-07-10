#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function, absolute_import, unicode_literals
from kubeshell.kubeshell import Kubeshell

import logging
logger = logging.getLogger(__name__)


def cli():
    kube_shell= Kubeshell()
    logger.info("session start")
    kube_shell.run_cli()

if __name__ == "__main__":
    cli()
