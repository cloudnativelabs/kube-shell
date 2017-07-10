from __future__ import absolute_import, unicode_literals, print_function
from subprocess import check_output
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import logging
import shlex
import json
import os
import os.path

from kubeshell.client import KubernetesClient


class KubectlCompleter(Completer):

    def __init__(self):
        self.all_commands = []
        self.all_args = []
        self.all_opts = []
        self.global_opts = []
        self.inline_help = True
        self.namespace = ""
        self.kube_client = KubernetesClient()
        self.logger = logging.getLogger(__name__)

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/cli.json')
            with open(DATA_PATH) as json_file:
                self.kubectl_dict = json.load(json_file)
            self.populate_cmds_args_opts(self.kubectl_dict)
        except Exception as ex:
            self.logger.error("got an exception" + ex.message)

    def set_inline_help(self, val):
        self.inline_help = val

    def set_namespace(self, namespace):
        self.namespace = namespace

    def populate_cmds_args_opts(self, key_map):
        for key in key_map.keys():
            self.all_commands.append(key)
            self.all_args.extend(key_map[key]['args'])
            if key == "kubectl":
                for opt in key_map[key]['options'].keys():
                    self.global_opts.append(opt)
            else:
                for opt in key_map[key]['options'].keys():
                    self.all_opts.append(opt)

            self.populate_cmds_args_opts(key_map[key]['subcommands'])

    # Below is the grammer of how kubectl expects and parses argument, commands and options
    # kubectl (global option)* command (global option | local option)* (subcommand (global option | local option)*)* (arg) (global option | local option)*
    # This method parse command, args, global flags, local flags from the text before cursor and suggest based on that return state,
    # inner most command seen, arg if any, and pass the dict corresponding to the command
    #
    # states:
    #
    #   INIT: this is starting state. In this state only 'kubectl' is expected as token
    #
    #   KUBECTL: State when first token is 'kubectl' and need to handle second token. In this state only commands of
    #           kubectl or one or more global options can be specified
    #
    #   KUBECTL_CMD: State representing case where we have received 'kubectl' and a 'command'. In this state either args, subcommands
    #           global options, or local options specifc to the commands can be specified
    #
    #   KUBECTL_ARG: In this state only global or local options for the commands can be specified. And also
    #          name os the resource like pods can be specified .We will reach this
    #          state from KUBCTL_CMD when we parse arg for a command
    #
    #   KUBECTL_LEAF: In this state only global or local options for the commands can be specified. We will reach this
    #          state from KUBCTL_CMD when we longer have any sub-commands or args for the previous command
    #
    def parse_tokens(self, cmdline):
        tokens = []
        if cmdline is not None:
            cmdline = cmdline.strip()
            tokens = shlex.split(cmdline)

        state = "INIT"
        index = 0
        key_map = self.kubectl_dict
        last_token = False

        command = ""
        arg = ""
        namespace = self.namespace

        for index, token in enumerate(tokens):

            # if --all-namespaces or --namespace option is passed overide the namespace
            # info from the kubeconfig with namespace found below logic
            if token == "--all-namespaces":
                namespace = "all"
            if token.startswith("--namespace"):
                if "=" in token:
                    namespace = token.split("=")[1]
            if tokens[index-1] == "--namespace":
                namespace = token

            if state == "INIT" and tokens[0] == "kubectl":
                state = "KUBECTL"
                key_map = key_map['kubectl']
                command = "kubectl"
                continue
            elif state == "KUBECTL":
                if token.startswith("--"):
                    continue
                if token in key_map['subcommands'].keys():
                    state = "KUBECTL_CMD"
                    key_map = key_map['subcommands'][token]
                    command = token
                continue
            elif state == "KUBECTL_CMD":
                if token.startswith("--"):
                    continue
                if token in key_map['subcommands'].keys():
                    state = "KUBECTL_CMD"
                    key_map = key_map['subcommands'][token]
                    command = token
                    continue
                if token in key_map['args']:
                    state = "KUBECTL_ARG"
                    arg = token
                    continue
                continue
            elif state == "KUBECTL_ARG":
                if token.startswith("--"):
                    continue
                resources = self.kube_client.get_resource(arg)
                if resources:
                    for resource_name, namespace in resources:
                        if token == resource_name:
                            state = "KUBECTL_LEAF"
                            continue
                continue
            elif state == "KUBECTL_LEAF":
                if token.startswith("--"):
                    continue
                continue
        return state, command, arg, key_map, namespace

    def get_completions(self, document, complete_event, smart_completion=None):

        word_before_cursor = document.get_word_before_cursor(WORD=True)

        tokens = []
        cmdline = document.text_before_cursor
        if cmdline is not None:
            cmdline = cmdline.strip()
            try:
                tokens = shlex.split(cmdline)
            except:
                return

        state, command, arg, key_map, namespace = self.parse_tokens(cmdline)

        top_level_commands = ["kubectl", "clear", "exit"]
        if state == "INIT":
            if len(tokens) == 0:
                for suggestion in top_level_commands:
                    yield Completion(suggestion)
                return
            if len(tokens) == 1 and word_before_cursor == tokens[0]:
                suggestions = fuzzyfinder(tokens[0], top_level_commands)
                for suggestion in suggestions:
                    yield Completion(suggestion, -len(tokens[0]))
        elif state == "KUBECTL":
            last_token = tokens[-1]
            self.help_msg = ""
            if word_before_cursor == last_token:
                if last_token.startswith("--"):
                    if last_token in self.global_opts:
                        return
                    global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                    for global_opt in global_opt_suggestions:
                        if self.inline_help:
                            self.help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                        yield Completion(global_opt, -len(word_before_cursor), display_meta=self.help_msg)
                else:
                    suggestions = fuzzyfinder(last_token, key_map['subcommands'].keys())
                    for suggestion in suggestions:
                        if self.inline_help:
                            self.help_msg = key_map['subcommands'][suggestion]['help']
                        yield Completion(suggestion, -len(last_token), display=suggestion, display_meta=self.help_msg)
            if word_before_cursor == "":
                if last_token == "--namespace":
                    namespaces = self.kube_client.get_resource("namespace")
                    for ns in namespaces:
                        yield Completion(ns[0])
                    return
                for cmd in key_map['subcommands'].keys():
                    if self.inline_help:
                        self.help_msg = key_map['subcommands'][cmd]['help']
                    yield Completion(cmd, display=cmd, display_meta=self.help_msg)
        elif state == "KUBECTL_CMD":
            last_token = tokens[-1]
            self.help_msg = ""
            if word_before_cursor == last_token:
                if last_token.startswith("--"):
                    if last_token in self.global_opts or last_token in key_map['options'].keys():
                        return
                    else:
                        command_opts = fuzzyfinder(word_before_cursor, key_map['options'].keys())
                        for command_opt in command_opts:
                            if self.inline_help:
                                self.help_msg = key_map['options'][command_opt]['help']
                            yield Completion(command_opt, -len(word_before_cursor), display=command_opt, display_meta=self.help_msg)
                        global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                        for global_opt in global_opt_suggestions:
                            if self.inline_help:
                                self.help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                            yield Completion(global_opt, -len(word_before_cursor), display=global_opt, display_meta=self.help_msg)
                elif last_token != command:
                    subcommands = key_map['subcommands'].keys()
                    if len(subcommands) > 0 and last_token not in subcommands:
                        suggestions = fuzzyfinder(last_token, subcommands)
                        for suggestion in suggestions:
                            if self.inline_help:
                                self.help_msg = key_map['subcommands'][suggestion]['help']
                            yield Completion(suggestion, -len(last_token), display=suggestion, display_meta=self.help_msg)
                    args = key_map['args']
                    if len(args) > 0 and last_token not in args:
                        suggestions = fuzzyfinder(last_token, args)
                        for arg in suggestions:
                            yield Completion(arg, -len(last_token))
            elif word_before_cursor == "":
                if last_token == "--namespace":
                    namespaces = self.kube_client.get_resource("namespace")
                    for ns in namespaces:
                        yield Completion(ns[0])
                    return
                subcommands = key_map['subcommands'].keys()
                for subcommand in subcommands:
                    if self.inline_help:
                        self.help_msg = key_map['subcommands'][subcommand]['help']
                    yield Completion(subcommand, display=subcommand, display_meta=self.help_msg)
                args = key_map['args']
                for arg in args:
                    yield Completion(arg)
        elif state == "KUBECTL_ARG":
            last_token = tokens[-1]
            if word_before_cursor == "":
                if last_token == "--namespace":
                    namespaces = self.kube_client.get_resource("namespace")
                    for ns in namespaces:
                        yield Completion(ns[0])
                    return
                resources = self.kube_client.get_resource(arg, namespace)
                if resources:
                    for resourceName, namespace in resources:
                        yield Completion(resourceName, display=resourceName, display_meta=namespace)
        elif state == "KUBECTL_LEAF":
            last_token = tokens[-1]
            self.help_msg = ""
            if last_token.startswith("--"):
                if last_token in self.global_opts or last_token in key_map['options'].keys():
                    return
                else:
                    command_opts = fuzzyfinder(word_before_cursor, key_map['options'].keys())
                    for command_opt in command_opts:
                        if self.inline_help:
                            self.help_msg = key_map['options'][command_opt]['help']
                        yield Completion(command_opt, -len(word_before_cursor), display=command_opt, display_meta=self.help_msg)
                    global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                    for global_opt in global_opt_suggestions:
                        if self.inline_help:
                            help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                        yield Completion(global_opt, -len(word_before_cursor), display=global_opt, display_meta=self.help_msg)
            if last_token == "--namespace":
                namespaces = self.kube_client.get_resource("namespace")
                for ns in namespaces:
                    yield Completion(ns[0])
                return
        else:
            pass
        return
