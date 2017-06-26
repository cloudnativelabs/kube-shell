from pygments.lexer import RegexLexer
from pygments.lexer import words
from pygments.token import Keyword, Name, Operator, Generic, Literal, Text

from completer import KubectlCompleter

class KubectlLexer(RegexLexer):
    """Provides highlighting for commands, subcommands, arguments, and options.

    """
    completer = KubectlCompleter()

    tokens = {
        'root': [
            (words(
                tuple(['kubectl']),
                prefix=r'\b',
                suffix=r'\b'),
             Literal.String),
            (words(
                tuple(completer.all_args),
                prefix=r'\b',
                suffix=r'\b'),
             Keyword.Declaration),
            (words(
                tuple(completer.all_commands),
                prefix=r'\b',
                suffix=r'\b'),
             Name.Class),
            (words(
                tuple(completer.all_opts),
                prefix=r'',
                suffix=r'\b'),
            Operator.Word),
            (words(
                tuple(completer.global_opts),
                prefix=r'',
                suffix=r'\b'),
            Operator.Word),
            #Keyword.Declaration),
            # Everything else
            (r'.*\n', Text),
        ]
    }
