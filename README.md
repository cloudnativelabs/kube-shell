
**NOTE: WILL UPDATE THE STATUS WHEN ITS IN USABLE STATE. RIGHT NOW ITS IN FLUX**

# kube-shell

Kubernetes shell: An integrated shell for working with the Kubernetes CLI

Under the hood kube-shell still calls kubectl. Kube-shell aims to provide ease-of-use of kubectl and increasing productivity. 

## kube-shell features

#### Auto Completion of Commands and Options with in-line documentation

![](http://i.imgur.com/bAWZt4c.gif)

#### Fish-Style Auto Suggestions

![](http://i.imgur.com/ybka6d5.png)

#### Command History

You can use up-arrow and down-arrow to walk through the history of commands executed. Also up-arrow partial string matching is possible. For e.g. enter 'kubectl get' and use up-arrow and down-arrow to browse through all kubectl get commands. You could also use CTRL+r to search from the history of commands.

![](http://i.imgur.com/lHEMAYt.png)

#### Fuzzy Searching

![](http://i.imgur.com/DQExE7e.png)

#### Server Side Auto Completion

![](http://i.imgur.com/hbRy0Rr.gif)

#### vi editing mode

Press ESC you have all key bindings (w: next word, b: prev word) to move across the words.

## Installation

The kube-shell requires python and [`pip`](https://pypi.python.org/pypi/pip) to install. You can install the kube-shell using `pip`:
``` bash
    $ pip install kube-shell
```
## Usage

After installing kube-shell through pip, just run kube-shell

## Acknowledgement

Kube-shell is inspired by [AWS Shell](https://github.com/awslabs/aws-shell), [SAWS](https://github.com/donnemartin/saws) and uses awesome Python [prompt toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) 
