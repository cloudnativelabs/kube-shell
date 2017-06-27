#!/usr/bin/env python
import re
import ast
from kubeshell.__init__ import __version__
from setuptools import setup, find_packages

requires = [
    'prompt-toolkit>=1.0.0,<1.1.0',
    'Pygments>=2.1.3,<3.0.0',
    'fuzzyfinder>=1.0.0',
    'click>=4.0,<7.0',
]

setup(
    name='kube-shell',
    version=__version__,
    description='Kubernetes shell: An integrated shell for working with the Kubernetes CLI',
    author='Cloudnative Labs',
    url='https://github.com/cloudnativelabs/kube-shell',
    packages=find_packages(),
    package_data={'kubeshell': ['data/cli.json']},
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'kube-shell = kubeshell.main:cli',
        ]
    },
    license="Apache License 2.0",
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)
