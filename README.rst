kube-shell
==============

|Build Status| |PyPI version| |PyPI pyversions| |License| |Gitter chat|

Kube-shell: An integrated shell for working with the Kubernetes CLI

Under the hood kube-shell still calls kubectl. Kube-shell aims to
provide ease-of-use of kubectl and increasing productivity.

kube-shell features
-------------------

Auto Completion of Commands and Options with in-line documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: http://i.imgur.com/dfelkKr.gif
   :alt: 

Fish-Style Auto Suggestions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: http://i.imgur.com/7VciOuR.png
   :alt: 

Command History
^^^^^^^^^^^^^^^

You can use up-arrow and down-arrow to walk through the history of
commands executed. Also up-arrow partial string matching is possible.
For e.g. enter 'kubectl get' and use up-arrow and down-arrow to browse
through all kubectl get commands. You could also use CTRL+r to search
from the history of commands.

.. figure:: http://i.imgur.com/xsIM3QV.png
   :alt: 

Fuzzy Searching
^^^^^^^^^^^^^^^

.. figure:: http://i.imgur.com/tW9oAUO.png
   :alt: 

Server Side Auto Completion
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: http://i.imgur.com/RAfHXjx.gif
   :alt: 

Context information
^^^^^^^^^^^^^^^^^^^

Details of current context from kubeconfig is always readily displayed
on the bottom toolbar. By pressing F4 button you can switch between the
clusters and using F5 can switch between namespaces.

.. figure:: http://i.imgur.com/MJLgcj3.png
   :alt: 

vi editing mode
^^^^^^^^^^^^^^^

Press ESC you have all key bindings (w: next word, b: prev word) to move
across the words.

Installation
------------

The kube-shell requires python and
`pip <https://pypi.python.org/pypi/pip>`__ to install. You can
install the kube-shell using ``pip``:

.. code:: bash

        $ pip install kube-shell

Usage
-----

After installing kube-shell through pip, just run kube-shell to bring up
shell.

At the kube-shell command prompt you can run exit or press F10 to exit
the shell. You can clear the screen by running clear command.

By default drop-down suggestion list also displays in-line
documentation, you can turn on/off inline documnetation by pressing F4
button.

You can run any shell command by prefixing command with "!". For e.g.
!ls would list from the current directory.

Under the hood
--------------

Other than generation of suggestions all heavy lifting is done by
Python's `prompt
toolkit <https://github.com/jonathanslenders/python-prompt-toolkit>`__,
`Pygments <http://pygments.org>`__ libraries.

A GO `program <misc/python_eats_cobra.go>`__ is used to generate
kubectl's commands, subcommands, arguments, global options and local
options in `json <kubeshell/data/cli.json>`__ format. Kube-shell uses
generated json file to suggest commands, subcommands, options and args.
For server side completion kube-shell uses
`client-python <https://github.com/kubernetes-incubator/client-python>`__
libray to fetch the resources.

Status
------

Kube-shell should be useful now. But given that its aim is to increase
productivity and easy of use, it can be improved in a number of ways. If
you have suggestions for improvements or new features, or run into a bug
please open an issue
`here <https://github.com/cloudnativelabs/kube-shell/issues>`__ or chat
in the `Gitter <https://gitter.im/kube-shell/Lobby>`__.

Acknowledgement
---------------

Kube-shell is inspired by `AWS
Shell <https://github.com/awslabs/aws-shell>`__,
`SAWS <https://github.com/donnemartin/saws>`__ and uses awesome Python
`prompt
toolkit <https://github.com/jonathanslenders/python-prompt-toolkit>`__

.. |Build Status| image:: https://travis-ci.org/cloudnativelabs/kube-shell.svg?branch=master
   :target: https://travis-ci.org/cloudnativelabs/kube-shell
.. |PyPI version| image:: https://badge.fury.io/py/kube-shell.svg
   :target: https://badge.fury.io/py/kube-shell
.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/ansicolortags.svg
   :target: https://pypi.python.org/pypi/kube-shell/
.. |License| image:: http://img.shields.io/:license-apache-blue.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0.html
.. |Gitter chat| image:: http://badges.gitter.im/kube-shell/Lobby.svg
   :target: https://gitter.im/kube-shell/Lobby
