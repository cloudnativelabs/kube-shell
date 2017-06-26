from __future__ import unicode_literals, print_function

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle

from style import StyleFactory
from completer import KubectlCompleter
from lexer import KubectlLexer

import os
import click
import sys
import subprocess

history = FileHistory(os.path.expanduser('~/.kube-shell/history'))

class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)

completer = KubectlCompleter()

while 1:
    user_input = prompt('kube-shell> ',
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            style=StyleFactory("vim").style,
            lexer=KubectlLexer,
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
