"""Tests for Endpoint._compute_gate (permission gate extraction)."""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../flow2code')))

from lib.types import Endpoint


def _mod(perm_map=None):
    """Minimal Module stub: only .permissions (id -> object with .name) is used."""
    perms = {}
    for pid, name in (perm_map or {}).items():
        perms[pid] = SimpleNamespace(id=pid, name=name)
    return SimpleNamespace(permissions=perms)


class TestComputeGate(unittest.TestCase):
    def test_public(self):
        self.assertEqual(Endpoint._compute_gate({"public": True}, _mod()), "public")

    def test_logged(self):
        self.assertEqual(Endpoint._compute_gate({"logged": True}, _mod()), "logged")

    def test_logged_wins_over_specific_perms(self):
        perms = {"logged": True, "perm.a": True}
        self.assertEqual(Endpoint._compute_gate(perms, _mod({"perm.a": "user.list"})), "logged")

    def test_single_permission(self):
        perms = {"public": False, "logged": False, "perm.a": True}
        self.assertEqual(Endpoint._compute_gate(perms, _mod({"perm.a": "user.list"})), ["user.list"])

    def test_multiple_permissions(self):
        perms = {"perm.a": True, "perm.b": True}
        mod = _mod({"perm.a": "user.list", "perm.b": "user.delete"})
        self.assertEqual(Endpoint._compute_gate(perms, mod), ["user.list", "user.delete"])

    def test_admins_maps_to_system_admin(self):
        self.assertEqual(Endpoint._compute_gate({"admins": True}, _mod()), ["system.admin"])

    def test_no_flag_set_is_none(self):
        perms = {"public": False, "logged": False, "admins": False, "perm.a": False}
        self.assertIsNone(Endpoint._compute_gate(perms, _mod({"perm.a": "user.list"})))

    def test_empty_permissions_is_none(self):
        self.assertIsNone(Endpoint._compute_gate({}, _mod()))

    def test_unknown_permission_id_ignored(self):
        perms = {"perm.missing": True}
        self.assertIsNone(Endpoint._compute_gate(perms, _mod()))


if __name__ == "__main__":
    unittest.main()
