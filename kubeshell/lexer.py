from __future__ import print_function, absolute_import
from pygments.lexer import RegexLexer
from pygments.lexer import words
from pygments.token import Keyword, Name, Operator, Generic, Literal, Text

from kubeshell.completer import KubectlCompleter

class KubectlLexer(RegexLexer):
    """Provides highlighting for commands, subcommands, arguments, and options.

    """
    completer = KubectlCompleter()

    tokens = {
        'root': [
            (words(
                tuple(['kubectl', 'clear', 'exit']),
                prefix=r'\b',
                suffix=r'\b'),
             Literal.String),
            # (words(
            #     tuple(completer.all_commands),
            #     prefix=r'\b',
            #     suffix=r'\b'),
            #  Name.Class),
            # (words(
            #     tuple(completer.all_args),
            #     prefix=r'\b',
            #     suffix=r'\b'),
            #  Name.Class),
            # (words(
            #     tuple(completer.all_opts),
            #     prefix=r'',
            #     suffix=r'\b'),
            # Keyword),
            # (words(
            #     tuple(completer.global_opts),
            #     prefix=r'',
            #     suffix=r'\b'),
            # Keyword),
            # Everything else
            (r'.*\n', Text),
        ]
    }
