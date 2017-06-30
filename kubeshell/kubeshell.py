from __future__ import print_function, absolute_import, unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pygments.style import Style
from pygments.token import Token
from pygments.token import Keyword, Name, Operator, Generic, Literal, Text
from pygments.styles.default import DefaultStyle
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys

from kubeshell.style import StyleFactory
from kubeshell.completer import KubectlCompleter
from kubeshell.lexer import KubectlLexer
from kubeshell.toolbar import Toolbar

import os
import click
import sys
import subprocess
import yaml


inline_help=True


registry = load_key_bindings_for_prompt()
completer = KubectlCompleter()

class Kubeshell(object):

    def __init__(self, refresh_resources=True):
        self.history = FileHistory(os.path.expanduser("~/.kube/shell/history"))
        if not os.path.exists(os.path.expanduser("~/.kube/shell/")):
            os.makedirs(os.path.expanduser("~/.kube/shell/"))
        self.toolbar = Toolbar(self.get_cluster_name, self.get_namespace, self.get_user, self.get_inline_help)

        self.clustername = self.user = ""
        self.namespace = "default"

    @registry.add_binding(Keys.F4)
    def _(event):
        global inline_help
        if inline_help:
            inline_help = False
        else:
            inline_help = True
        completer.set_inline_help(inline_help)

    @registry.add_binding(Keys.F10)
    def _(event):
        sys.exit()

    def get_cluster_name(self):
        return self.clustername

    def get_namespace(self):
        return self.namespace

    def get_user(self):
        return self.user

    def get_inline_help(self):
        return inline_help

    def parse_kubeconfig(self):
        self.clustername = self.user = ""
        self.namespace = "default"

        if not os.path.exists(os.path.expanduser("~/.kube/config")):
            return

        with open(os.path.expanduser("~/.kube/config"), "r") as fd:
            docs = yaml.load_all(fd)
            for doc in docs:
                current_context = ""
                for k,v in doc.items():
                    if k == "current-context":
                        current_context = v
                for k,v in doc.items():
                    if k == "contexts":
                        for context in v:
                            if context['name'] == current_context:
                                if 'cluster' in context['context']:
                                    self.clustername = context['context']['cluster']
                                if 'namespace' in context['context']:
                                    self.namespace = context['context']['namespace']
                                if 'user' in context['context']:
                                    self.user = context['context']['user']

    def run_cli(self):

        def get_title():
            return "kube-shell"

        if not os.path.exists(os.path.expanduser("~/.kube/config")):
            click.secho('Kube-shell uses ~/.kube/config for server side completion. Could not find ~/.kube/config. \
                    Server side completion functionality may not work.', fg='red', blink=True, bold=True)
        while True:
            global inline_help
            try:
                self.parse_kubeconfig()
            except:
                # TODO: log errors to log file
                pass
            user_input = prompt('kube-shell> ',
                        history=self.history,
                        auto_suggest=AutoSuggestFromHistory(),
                        style=StyleFactory("vim").style,
                        lexer=KubectlLexer,
                        get_title=get_title,
                        enable_history_search=False,
                        get_bottom_toolbar_tokens=self.toolbar.handler,
                        vi_mode=True,
                        key_bindings_registry=registry,
                        completer=completer)
            if user_input == "clear":
                click.clear()
            elif user_input == "exit":
                sys.exit()
            if user_input:
                if '-o' in user_input and 'json' in user_input:
                    user_input = user_input + ' | pygmentize -l json'
                p = subprocess.Popen(user_input, shell=True)
                p.communicate()
