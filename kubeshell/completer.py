from __future__ import absolute_import, unicode_literals, print_function
from subprocess import check_output
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import shlex
import json
import os
import os.path
from kubernetes import client, config

class KubectlCompleter(Completer):

    def __init__(self):
        self.all_commands = []
        self.all_args = []
        self.all_opts = []
        self.global_opts = []
        self.inline_help = True

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/cli.json')
            with open(DATA_PATH) as json_file:
                self.kubectl_dict = json.load(json_file)
            self.populate_cmds_args_opts(self.kubectl_dict)
        except Exception as ex:
            print("got an exception" + ex.message)

    def set_inline_help(self, val):
        self.inline_help = val

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
        for token in tokens:
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
                resources = self.get_resources(arg, "default")
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
        return state, command, arg, key_map

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

        state, command, arg, key_map = self.parse_tokens(cmdline)

        if state == "INIT":
            self.help_msg = ""
            if self.inline_help:
                self.help_msg = display_meta=key_map['kubectl']['help']
            if len(tokens) == 0:
                yield Completion("kubectl", start_position=0, display="kubectl", display_meta=self.help_msg)
                return
            if len(tokens) == 1 and word_before_cursor == tokens[0]:
                suggestions = fuzzyfinder(tokens[0], ['kubectl'])
                for suggestion in suggestions:
                    yield Completion(suggestion, -len(tokens[0]), display="kubectl", display_meta=self.help_msg)
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
                subcommands = key_map['subcommands'].keys()
                for subcommand in subcommands:
                    if self.inline_help:
                        self.help_msg = key_map['subcommands'][subcommand]['help']
                    yield Completion(subcommand, display=subcommand, display_meta=self.help_msg)
                args = key_map['args']
                for arg in args:
                    yield Completion(arg)
        elif state == "KUBECTL_ARG":
            if word_before_cursor == "":
                resources = self.get_resources(arg, "default")
                if resources:
                    for resourceName, namespace in self.get_resources(arg, "default"):
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
        else:
            pass
        return

    def get_resources(self, resource, namespace="all"):
        resources = []
        config.load_kube_config()

        v1 = client.CoreV1Api()
        v1Beta1 = client.AppsV1beta1Api()
        extensionsV1Beta1 = client.ExtensionsV1beta1Api()
        autoscalingV1Api = client.AutoscalingV1Api()
        rbacAPi = client.RbacAuthorizationV1beta1Api()
        batchV1Api = client.BatchV1Api()
        batchV2Api = client.BatchV2alpha1Api()

        ret = None
        namespaced_resource = True

        if resource == "pod":
            ret = v1.list_pod_for_all_namespaces(watch=False)
        elif resource == "service":
            ret = v1.list_service_for_all_namespaces(watch=False)
        elif resource == "deployment":
            ret = v1Beta1.list_deployment_for_all_namespaces(watch=False)
        elif resource == "statefulset":
            ret = v1Beta1.list_stateful_set_for_all_namespaces(watch=False)
        elif resource == "node":
            namespaced_resource = False
            ret = v1.list_node(watch=False)
        elif resource == "namespace":
            namespaced_resource = False
            ret = v1.list_namespace(watch=False)
        elif resource == "daemonset":
            ret = extensionsV1Beta1.list_daemon_set_for_all_namespaces(watch=False)
        elif resource == "networkpolicy":
            ret = extensionsV1Beta1.list_network_policy_for_all_namespaces(watch=False)
        elif resource == "thirdpartyresource":
            namespaced_resource = False
            ret = extensionsV1Beta1.list_third_party_resource(watch=False)
        elif resource == "replicationcontroller":
            ret = v1.list_replication_controller_for_all_namespaces(watch=False)
        elif resource == "replicaset":
            ret = extensionsV1Beta1.list_replica_set_for_all_namespaces(watch=False)
        elif resource == "ingress":
            ret = extensionsV1Beta1.list_ingress_for_all_namespaces(watch=False)
        elif resource == "endpoints":
            ret = v1.list_endpoints_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "event":
            ret = v1.list_event_for_all_namespaces(watch=False)
        elif resource == "limitrange":
            ret = v1.list_limit_range_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "persistentvolume":
            namespaced_resource = False
            ret = v1.list_persistent_volume(watch=False)
        elif resource == "secret":
            ret = v1.list_secret_for_all_namespaces(watch=False)
        elif resource == "resourcequota":
            ret = v1.list_resource_quota_for_all_namespaces(watch=False)
        elif resource == "componentstatus":
            namespaced_resource = False
            ret = v1.list_component_status(watch=False)
        elif resource == "podtemplate":
            ret = v1.list_pod_template_for_all_namespaces(watch=False)
        elif resource == "serviceaccount":
            ret = v1.list_service_account_for_all_namespaces(watch=False)
        elif resource == "horizontalpodautoscaler":
            ret = autoscalingV1Api.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
        elif resource == "clusterrole":
            namespaced_resource = False
            ret = rbacAPi.list_cluster_role(watch=False)
        elif resource == "clusterrolebinding":
            namespaced_resource = False
            ret = rbacAPi.list_cluster_role_binding(watch=False)
        elif resource == "job":
            ret = batchV1Api.list_job_for_all_namespaces(watch=False)
        elif resource == "cronjob":
            ret = batchV2Api.list_cron_job_for_all_namespaces(watch=False)
        elif resource == "scheduledjob":
            ret = batchV2Api.list_scheduled_job_for_all_namespaces(watch=False)

        if ret:
            for i in ret.items:
                if namespace == "all" or not namespaced_resource:
                    resources.append((i.metadata.name, i.metadata.namespace))
                elif namespace == i.metadata.namespace:
                    resources.append((i.metadata.name, i.metadata.namespace))
            return resources
        return None

