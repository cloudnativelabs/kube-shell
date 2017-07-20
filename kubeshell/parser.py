from __future__ import absolute_import, unicode_literals, print_function
import json
import os

import logging
logger = logging.getLogger(__name__)

from kubeshell.client import KubernetesClient


class Option(object):
    """ Option represents an optional local flag in kubectl """

    def __init__(self, name, helptext):
        self.name = name
        self.helptext = helptext


class CommandTree(object):
    """ CommandTree represents the tree node of a kubectl command line """

    def __init__(self, node=None, helptext=None, children=None, localFlags=None):
        self.node = node
        self.help = helptext
        self.children = children if children else list()
        self.localFlags = localFlags if localFlags else list()

    def __str__(self):
        return "Node: %s, Help: %s\n Flags: %s\n Children: %s" % (self.node, self.help, self.localFlags, self.children)


class Parser(object):
    """ Parser builds and walks the syntax tree of kubectl """

    def __init__(self, apiFile):
        self.json_api = apiFile
        self.schema = dict()
        self.globalFlags = list()
        with open(self.json_api) as api:
            self.schema = json.load(api)
        self.ast = CommandTree("kubectl")
        self.ast = self.build(self.ast, self.schema.get("kubectl"))
        self.kube_client = KubernetesClient()

    def build(self, root, schema):
        """ Build the syntax tree for kubectl command line """
        if schema.get("subcommands") and schema["subcommands"]:
            for subcmd, childSchema in schema["subcommands"].items():
                child = CommandTree(node=subcmd)
                child = self.build(child, childSchema)
                root.children.append(child)
        # {args: {}, options: {}, help: ""}
        root.help = schema.get("help")
        for name, desc in schema.get("options").items():
            if root.node == "kubectl":  # register global flags
                self.globalFlags.append(Option(name, desc["help"]))
            root.localFlags.append(Option(name, desc["help"]))
        for arg in schema.get("args"):
            node = CommandTree(node=arg)
            root.children.append(node)
        return root

    def print_tree(self, root, indent=0):
        indentter = '{:>{width}}'.format(root.node, width=indent)
        print(indentter)
        for child in root.children:
            self.print_tree(root=child, indent=indent+2)

    def parse_tokens(self, tokens):
        """ Parse a sequence of tokens

        returns tuple of (parsed tokens, suggestions)
        """
        if len(tokens) == 1:
            return list(), tokens, {"kubectl": self.ast.help}
        else:
            tokens.reverse()
        parsed, unparsed, suggestions = self.treewalk(self.ast, parsed=list(), unparsed=tokens)
        if not suggestions and unparsed:
            # TODO: @vogxn: This is hack until we include expected value types for each option and argument.
            # Whenver we recieve no suggestions but are left with unparsed tokens we pop the value and walk the
            # tree again without values
            logger.debug("unparsed tokens remain, possible value encountered")
            unparsed.pop()
            parsed.reverse()
            unparsed.extend(parsed)
            logger.debug("resuming treewalk with tokens: %s", unparsed)
            return self.treewalk(self.ast, parsed=list(), unparsed=unparsed)
        else:
            return parsed, unparsed, suggestions

    def treewalk(self, root, parsed, unparsed):
        """ Recursively walks the syntax tree at root and returns
        the items parsed, unparsed and possible suggestions """
        suggestions = dict()
        if not unparsed:
            logger.debug("no tokens left unparsed. returning %s, %s", parsed, suggestions)
            return parsed, unparsed, suggestions

        token = unparsed.pop().strip()
        logger.debug("begin parsing at %s w/ tokens: %s", root.node, unparsed)
        if root.node == token:
            logger.debug("root node: %s matches next token:%s", root.node, token)
            parsed.append(token)
            if self.peekForOption(unparsed):  # check for localFlags and globalFlags
                logger.debug("option(s) upcoming %s", unparsed)
                parsed_opts, unparsed, suggestions = self.evalOptions(root, list(), unparsed[:])
                if parsed_opts:
                    logger.debug("parsed option(s): %s", parsed_opts)
                    parsed.extend(parsed_opts)
            if unparsed and not self.peekForOption(unparsed):  # unparsed bits without options
                logger.debug("begin subtree %s parsing", root.node)
                for child in root.children:
                    parsed_subtree, unparsed, suggestions = self.treewalk(child, list(), unparsed[:])
                    if parsed_subtree:  # subtree returned further parsed tokens
                        parsed.extend(parsed_subtree)
                        logger.debug("subtree at: %s has matches. %s, %s", child.node, parsed, unparsed)
                        break
                else:
                    # no matches found in command tree
                    # return children of root as suggestions
                    logger.debug("no matches in subtree: %s. returning children as suggestions", root.node)
                    for child in root.children:
                        suggestions[child.node] = child.help
        else:
            logger.debug("no token or option match")
            unparsed.append(token)
        return parsed, unparsed, suggestions

    def peekForOption(self, unparsed):
        """ Peek to find out if next token is an option """
        if unparsed and unparsed[-1].startswith("--"):
            return True
        return False

    def evalOptions(self, root, parsed, unparsed):
        """ Evaluate only the options and return flags as suggestions """
        logger.debug("parsing options at tree: %s with p:%s, u:%s", root.node, parsed, unparsed)
        suggestions = dict()
        token = unparsed.pop().strip()

        parts = token.partition('=')
        if parts[-1] != '':  # parsing for --option=value type input
            token = parts[0]

        allFlags = root.localFlags + self.globalFlags
        for flag in allFlags:
            if flag.name == token:
                logger.debug("matched token: %s with flag: %s", token, flag.name)
                parsed.append(token)
                if self.peekForOption(unparsed):  # recursively look for further options
                    parsed, unparsed, suggestions = self.evalOptions(root, parsed, unparsed[:])
                # elif token == "--namespace":
                #     namespaces = [('default', None), ('minikube', None), ('gitlab', None)]  # self.kube_client.get_resource("namespace")
                #     suggestions = dict(namespaces)
                break
        else:
            logger.debug("no flags match, returning allFlags suggestions")
            for flag in allFlags:
                suggestions[flag.name] = flag.helptext

        if suggestions:  # incomplete parse, replace token
            logger.debug("incomplete option: %s provided. returning suggestions", token)
            unparsed.append(token)
        return parsed, unparsed, suggestions

if __name__ == '__main__':
    parser = Parser('/Users/tsp/workspace/py/kube-shell/kubeshell/data/cli.json')
    p, _, s = parser.treewalk(parser.ast, parsed=list(), unparsed=['--', '--tcp 900:8080', 'nodeport', 'service', 'create', 'kubectl'])
    print(p, s)
