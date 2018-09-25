#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, print_function, unicode_literals

import logging

from kubeshell.kubeshell import Kubeshell

logger = logging.getLogger(__name__)


def cli():
    kube_shell = Kubeshell()
    logger.info("session start")
    kube_shell.run_cli()


if __name__ == "__main__":
    cli()
