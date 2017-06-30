from __future__ import unicode_literals
import unittest
import pip
import pexpect
import unittest

class CliTest(unittest.TestCase):

    def test_run_cli(self):
        self.cli = None
        self.step_run_cli()
        self.step_see_prompt()

    def step_run_cli(self):
        self.cli = pexpect.spawnu('kube-shell')

    def step_see_prompt(self):
        self.cli.expect('kube-shell> ')

if __name__ == "__main__":
    unittest.main()
