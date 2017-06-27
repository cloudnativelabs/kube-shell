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
        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/cli.json')
            with open(DATA_PATH) as json_file:
                self.kubectl_dict = json.load(json_file)
            self.populate_cmds_args_opts(self.kubectl_dict)
        except Exception as ex:
            print "got an exception" + ex.message

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

    # TODO: Need cleanup to make code more readable and understandable
    #
    # Below is the grammer of how kubectl expects and parses argument, commands and options
    #
    # kubectl (global option)* command (global option | local option)* (subcommand (global option | local option)*)* (arg) (global option | local option)*
    #
    # We use four states to parse command, args, global flags, local flags and suggest based on that
    #
    # states:
    #
    #   INIT: this is starting state. In this state we only expect 'kubectl' as first token
    #
    #   KUBCTL: State when first token is 'kubectl' and need to handle second token. In this state only commands of
    #           kubectl or one or more global options can be specified
    #
    #   KUBCTL_CMD: State representing case where we have received 'kubectl' and a 'command'. In this state either args, subcommands
    #           global options, or local options specifc to the commands can be specified
    #
    #   KUBCTL_LEAF: In this state only global or local options for the commands can be specified. We will reach this
    #          state from KUBCTL_CMD when we longer have any sub-commands or args for the previous command
    #
    def get_completions(self, document, complete_event, smart_completion=None):
        cmdline = document.text_before_cursor
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        tokens = []
        if cmdline is not None:
            cmdline = cmdline.strip()
            tokens = shlex.split(cmdline)

        state = "INIT"
        index = 0
        key_map = self.kubectl_dict
        last_token = False

        if len(tokens) == 0:
            yield Completion("kubectl", start_position=0, display="kubectl", display_meta=key_map['kubectl']['help'])
            return

        command = "kubectl"
        while index < len(tokens):
            last_token = (index == (len(tokens) - 1))
            if state == "INIT":
                if last_token:
                    if tokens[0] != "kubectl":
                        suggestions = fuzzyfinder(tokens[0], ['kubectl'])
                        for suggestion in suggestions:
                            yield Completion(suggestion, -len(tokens[0]), display="kubectl", display_meta=key_map['kubectl']['help'] )
                        return
                    elif word_before_cursor == "":
                        for cmd in key_map['kubectl']['subcommands'].keys():
                            yield Completion(cmd, display=cmd, display_meta=key_map['kubectl']['subcommands'][cmd]['help'])
                        return
                    elif word_before_cursor == "kubectl":
                        return
                elif tokens[0] == "kubectl":
                    index = index + 1
                    state = "KUBCTL"
                    key_map = key_map['kubectl']
                    continue
            elif state == "KUBCTL":
                if tokens[index].startswith("--"):
                    if last_token:
                        if word_before_cursor == tokens[index]:
                            if tokens[index] in self.global_opts:
                                return
                            else:
                                global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                                for global_opt in global_opt_suggestions:
                                    help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                                    yield Completion(global_opt, -len(word_before_cursor), display_meta=help_msg)
                                return
                        elif word_before_cursor == "":
                            for cmd in key_map['subcommands'].keys():
                                yield Completion(cmd, display=cmd, display_meta=key_map['subcommands'][cmd]['help'])
                            return
                    else:
                        index = index + 1
                        continue
                elif last_token and tokens[index] not in key_map['subcommands'].keys():
                    if word_before_cursor == tokens[index]:
                        suggestions = fuzzyfinder(tokens[index], key_map['subcommands'].keys())
                        for suggestion in suggestions:
                            yield Completion(suggestion, -len(tokens[index]), display=suggestion, display_meta=key_map['subcommands'][suggestion]['help'])
                        return
                    return
                elif not last_token and tokens[index] in key_map['subcommands'].keys():
                    key_map = key_map['subcommands'][tokens[index]]
                    command = command + "_" + tokens[index]
                    index = index + 1
                    state = "KUBCTL_CMD"
                    continue
                elif last_token and tokens[index] in key_map['subcommands'].keys() and word_before_cursor == "":
                        subcommands = key_map['subcommands'][tokens[index]]['subcommands'].keys()
                        if len(subcommands) > 0:
                            for sub_cmd in subcommands:
                                help_msg = key_map['subcommands'][tokens[index]]['subcommands'][sub_cmd]['help']
                                yield Completion(sub_cmd, display=sub_cmd, display_meta=help_msg)
                            return
                        args =  key_map['subcommands'][tokens[index]]['args']
                        if len(args) > 0:
                            for arg in args:
                                yield Completion(arg)
                            return
                        for global_opt in self.global_opts:
                            help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                            yield Completion(global_opt,  display=global_opt, display_meta=help_msg)

                        for command_opt in key_map['subcommands'][tokens[index]]['options'].keys():
                            help_msg = key_map['subcommands'][tokens[index]]['options'][command_opt]['help']
                            yield Completion(command_opt, display=command_opt, display_meta=help_msg)
                        return
                return
            elif state == "KUBCTL_CMD":
                if tokens[index].startswith("--"):
                    if last_token:
                        if word_before_cursor == tokens[index]:
                            if tokens[index] in self.global_opts or tokens[index] in key_map['options'].keys():
                                return
                            else:
                                global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                                for global_opt in global_opt_suggestions:
                                    help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                                    yield Completion(global_opt, -len(word_before_cursor), display=global_opt, display_meta=help_msg)

                                command_opts = fuzzyfinder(word_before_cursor, key_map['options'].keys())
                                for command_opt in command_opts:
                                    help_msg = key_map['options'][command_opt]['help']
                                    yield Completion(command_opt, -len(word_before_cursor), display=command_opt, display_meta=help_msg)
                                return
                        elif word_before_cursor == "":
                            for cmd in key_map['subcommands'].keys():
                                yield Completion(cmd, display=cmd, display_meta= key_map['subcommands'][cmd]['help'])
                            return
                        return
                    else:
                        index = index + 1
                        continue
                elif tokens[index] in key_map['args']:
                    if not last_token:
                        state = "KUBCTL_LEAF"
                        index = index + 1
                        continue
                    else:
                        state = "KUBCTL_ARG"
                        continue
                elif tokens[index] in key_map['subcommands'].keys():
                    command = command + "_" + tokens[index]
                    if not last_token:
                        key_map = key_map['subcommands'][tokens[index]]
                        index = index + 1
                        continue
                    else:
                        if word_before_cursor == "":
                            subcommands = key_map['subcommands'][tokens[index]]['subcommands'].keys()
                            if len(subcommands) > 0:
                                for sub_cmd in subcommands:
                                    help_msg = key_map['subcommands'][tokens[index]]['subcommands'][sub_cmd]['help']
                                    yield Completion(sub_cmd, display=sub_cmd, display_meta=help_msg)
                                return
                            args =  key_map['subcommands'][tokens[index]]['args']
                            if len(args) > 0:
                                for arg in args:
                                    yield Completion(arg)
                                return
                            for global_opt in self.global_opts:
                                help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                                yield Completion(global_opt,  display=global_opt, display_meta=help_msg)
                            for command_opt in key_map['subcommands'][tokens[index]]['options'].keys():
                                help_msg = key_map['subcommands'][tokens[index]]['options'][command_opt]['help']
                                yield Completion(command_opt, display=command_opt, display_meta=help_msg)
                            return
                        return
                elif last_token and tokens[index] not in key_map['subcommands'].keys():
                    subcommands = key_map['subcommands'].keys()
                    if len(subcommands) > 0:
                        suggestions = fuzzyfinder(tokens[index], subcommands)
                        for suggestion in suggestions:
                            yield Completion(suggestion, -len(tokens[index]), display=suggestion, display_meta=key_map['subcommands'][suggestion]['help'])
                        return
                    args = key_map['args']
                    if len(args) > 0:
                        suggestions = fuzzyfinder(tokens[index], args)
                        for arg in suggestions:
                            yield Completion(arg, -len(tokens[index]))
                        return
                return
            elif state == "KUBCTL_ARG":
                resource = tokens[index]
                if last_token and word_before_cursor == "":
                    for resourceName, namespace in self.get_resources(resource, "default"):
                        yield Completion(resourceName, display=resourceName, display_meta=namespace)
                return
            elif state == "KUBCTL_LEAF":
                if tokens[index].startswith("--"):
                    if last_token:
                        if word_before_cursor == tokens[index]:
                            if tokens[index] in self.global_opts or tokens[index] in key_map['options'].keys():
                                return
                            else:
                                global_opt_suggestions = fuzzyfinder(word_before_cursor, self.global_opts)
                                for global_opt in global_opt_suggestions:
                                    help_msg = self.kubectl_dict['kubectl']['options'][global_opt]['help']
                                    yield Completion(global_opt, -len(word_before_cursor), display=global_opt, display_meta=help_msg)
                                command_opts = fuzzyfinder(word_before_cursor, key_map['options'].keys())
                                for command_opt in command_opts:
                                    help_msg = key_map['options'][command_opt]['help']
                                    yield Completion(command_opt, -len(word_before_cursor), display=command_opt, display_meta=help_msg)
                                return
                    else:
                        index = index +1
                        continue
                    return
                else:
                    return
        return

    def get_resources(self, resource, namespace):
        names = []
        config.load_kube_config()

        v1 = client.CoreV1Api()
        v1Beta1 = client.AppsV1beta1Api()
        extensionsV1Beta1 = client.ExtensionsV1beta1Api()
        autoscalingV1Api = client.AutoscalingV1Api()
        rbacAPi = client.RbacAuthorizationV1beta1Api()
        batchV1Api = client.BatchV1Api()
        batchV2Api = client.BatchV2alpha1Api()

        if resource == "pod":
            ret = v1.list_pod_for_all_namespaces(watch=False)
        elif resource == "service":
            ret = v1.list_service_for_all_namespaces(watch=False)
        elif resource == "deployment":
            ret = v1Beta1.list_deployment_for_all_namespaces(watch=False)
        elif resource == "statefulset":
            ret = v1Beta1.list_stateful_set_for_all_namespaces(watch=False)
        elif resource == "node":
            ret = v1.list_node(watch=False)
        elif resource == "namespace":
            ret = v1.list_namespace(watch=False)
        elif resource == "daemonset":
            ret = extensionsV1Beta1.list_daemon_set_for_all_namespaces(watch=False)
        elif resource == "networkpolicy":
            ret = extensionsV1Beta1.list_network_policy_for_all_namespaces(watch=False)
        elif resource == "thirdpartyresource":
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
            ret = v1.list_persistent_volume(watch=False)
        elif resource == "secret":
            ret = v1.list_secret_for_all_namespaces(watch=False)
        elif resource == "resourcequota":
            ret = v1.list_resource_quota_for_all_namespaces(watch=False)
        elif resource == "componentstatus":
            ret = v1.list_component_status(watch=False)
        elif resource == "podtemplate":
            ret = v1.list_pod_template_for_all_namespaces(watch=False)
        elif resource == "serviceaccount":
            ret = v1.list_service_account_for_all_namespaces(watch=False)
        elif resource == "horizontalpodautoscaler":
            ret = autoscalingV1Api.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
        elif resource == "clusterrole":
            ret = rbacAPi.list_cluster_role(watch=False)
        elif resource == "clusterrolebinding":
            ret = rbacAPi.list_cluster_role_binding(watch=False)
        elif resource == "job":
            ret = batchV1Api.list_job_for_all_namespaces(watch=False)
        elif resource == "cronjob":
            ret = batchV2Api.list_cron_job_for_all_namespaces(watch=False)
        elif resource == "scheduledjob":
            ret = batchV2Api.list_scheduled_job_for_all_namespaces(watch=False)
        for i in ret.items:
            names.append((i.metadata.name, i.metadata.namespace))
        return names

