"""Tests for the template-rejection -> non-zero exit wiring."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../flow2code')))

from flow2code import Flow2Code
from lib.template_base import TemplateBase


class _Template:
    """Fake template whose code() verdict is scripted per call."""

    def __init__(self, verdicts):
        self._verdicts = list(verdicts)
        self.calls = []

    def code(self, mod, flow, output):
        self.calls.append(mod)
        return self._verdicts.pop(0)


def _f2c(template, modules):
    f2c = Flow2Code.__new__(Flow2Code)
    f2c.template = template
    f2c.modules = modules
    return f2c


class TestExitWiring(unittest.TestCase):
    def test_all_ok_returns_true(self):
        t = _Template([None, True])
        self.assertTrue(_f2c(t, ["m1", "m2"]).code("out"))

    def test_one_rejection_returns_false(self):
        t = _Template([None, False, None])
        self.assertFalse(_f2c(t, ["m1", "m2", "m3"]).code("out"))

    def test_every_module_is_attempted_despite_a_rejection(self):
        t = _Template([False, None, None])
        _f2c(t, ["m1", "m2", "m3"]).code("out")
        self.assertEqual(t.calls, ["m1", "m2", "m3"])


class TestReportErrors(unittest.TestCase):
    def test_accumulates_and_prefixes(self):
        tb = TemplateBase()
        self.assertEqual(tb.errors, [])

        tb.report_errors(["first problem", "second problem"])

        self.assertEqual(tb.errors, ["first problem", "second problem"])


if __name__ == "__main__":
    unittest.main()
