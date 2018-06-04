from __future__ import absolute_import, unicode_literals, print_function
from subprocess import check_output
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import logging
import shlex
import json
import os
import os.path

from kubeshell.parser import Parser
from kubeshell.client import KubernetesClient
logger = logging.getLogger(__name__)


class KubectlCompleter(Completer):

    def __init__(self):
        self.inline_help = True
        self.namespace = ""
        self.kube_client = KubernetesClient()

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/cli.json')
            with open(DATA_PATH) as json_file:
                self.kubectl_dict = json.load(json_file)
            self.parser = Parser(DATA_PATH)
        except Exception as ex:
            logger.error("got an exception" + ex.message)

    def set_inline_help(self, val):
        self.inline_help = val

    def set_namespace(self, namespace):
        self.namespace = namespace

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        cmdline = document.text_before_cursor.strip()
        try:
            tokens = shlex.split(cmdline)
            _, _, suggestions = self.parser.parse_tokens(tokens)
            valid_keys = fuzzyfinder(word_before_cursor, suggestions.keys())
            for key in valid_keys:
                yield Completion(key, -len(word_before_cursor), display=key, display_meta=suggestions[key])
        except ValueError:
            pass
