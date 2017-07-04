#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function, absolute_import, unicode_literals
from kubeshell.kubeshell import Kubeshell

def cli():
    kube_shell= Kubeshell()
    kube_shell.run_cli()

if __name__ == "__main__":
    cli()
