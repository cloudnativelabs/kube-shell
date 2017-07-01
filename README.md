
# WIP kube-shell

[![Build Status](https://travis-ci.org/cloudnativelabs/kube-shell.svg?branch=master)](https://travis-ci.org/cloudnativelabs/kube-shell) [![PyPI version](https://badge.fury.io/py/kube-shell.svg)](https://badge.fury.io/py/kube-shell) [![License](http://img.shields.io/:license-apache-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

Kube-shell: An integrated shell for working with the Kubernetes CLI

Under the hood kube-shell still calls kubectl. Kube-shell aims to provide ease-of-use of kubectl and increasing productivity. 

## kube-shell features

#### Auto Completion of Commands and Options with in-line documentation

![](http://i.imgur.com/dfelkKr.gif)

#### Fish-Style Auto Suggestions

![](http://i.imgur.com/7VciOuR.png)

#### Command History

You can use up-arrow and down-arrow to walk through the history of commands executed. Also up-arrow partial string matching is possible. For e.g. enter 'kubectl get' and use up-arrow and down-arrow to browse through all kubectl get commands. You could also use CTRL+r to search from the history of commands.

![](http://i.imgur.com/xsIM3QV.png)

#### Fuzzy Searching

![](http://i.imgur.com/tW9oAUO.png)

#### Server Side Auto Completion

![](http://i.imgur.com/RAfHXjx.gif)

#### Context information

Details of current context from kubeconfig is always readily displayed on the bottom toolbar.

![](http://i.imgur.com/DAWCxa6.png)

#### vi editing mode

Press ESC you have all key bindings (w: next word, b: prev word) to move across the words.

## Installation

The kube-shell requires python and [`pip`](https://pypi.python.org/pypi/pip) to install. You can install the kube-shell using `pip`:
``` bash
    $ pip install kube-shell
```
## Usage

After installing kube-shell through pip, just run kube-shell to bring up shell.

At the kube-shell command prompt you can run exit or press F10 to exit the shell. You can clear the screen by running clear command.

By default drop-down suggestion list also displays in-line documentation, you can turn on/off inline documnetation by pressing F4 button.

You can run any shell command by prefixing command with "!". For e.g. !ls would list from the current directory.

## Under the hood

Other than generation of suggestions all heavy lifting is done by Python's [prompt toolkit](https://github.com/jonathanslenders/python-prompt-toolkit), [Pygments](http://pygments.org) libraries.

A GO [program](misc/python_eats_cobra.go) is used to generate kubectl's commands, subcommands, arguments, global options and local options in [json](kubeshell/data/cli.json) format. Kube-shell uses generated json file to suggest commands, subcommands, options and args. For server side completion kube-shell uses [client-python](https://github.com/kubernetes-incubator/client-python) libray to fetch the resources.

## Acknowledgement

Kube-shell is inspired by [AWS Shell](https://github.com/awslabs/aws-shell), [SAWS](https://github.com/donnemartin/saws) and uses awesome Python [prompt toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) 
