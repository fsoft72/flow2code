#!/usr/bin/env python3

"""
This script converts a flow file to code

Author: Fabio Rotondo <fabio.rotondo@gmail.com>

See: https://flow.liwe.org
"""

# remove deprecated warnings
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import argparse
import json
import os
import sys
import importlib.util

# append the path of this file in the python path
APP_PATH = os.path.dirname(os.path.realpath(__file__))

from lib.types import Module, Permission, Endpoint, Type, Enum, Function, Event

VERSION = "0.3.1"


class Flow2Code:
    # List of modules to be converted
    modules: list[Module] = []

    # Global variables
    permissions: dict[str, Permission] = {}
    endpoints: dict[str, Endpoint] = {}
    types: dict[str, Type] = {}
    enums: dict[str, Enum] = {}
    functions: dict[str, Function] = {}
    events: dict[str, Event] = {}

    # The template module instance
    template = None

    strict: bool = False

    def __init__(self, flow, template, strict, templates_dirs=None):
        self.strict = strict
        self.templates_dirs = templates_dirs or []

        self._open_flow(flow)
        self._open_template(template)

    def _open_flow(self, flow_fname):
        data = json.loads(open(flow_fname, "r").read())

        m = ""
        if "modules" in data:
            m = "modules"
        elif "mods" in data:
            m = "mods"

        if m:
            for mod in data[m].values():
                self.modules.append(Module(mod, self))
        else:
            self.modules.append(Module(data, self))

    def _open_template(self, template_name):
        # instance the template file from template_fname
        # and assign it to self.template

        search_dirs = [os.path.join(APP_PATH, "templates")] + self.templates_dirs
        fname = None
        for s_dir in search_dirs:
            candidate = os.path.join(s_dir, template_name, "template.py")
            if os.path.exists(candidate):
                fname = candidate
                break

        if not fname:
            print("ERROR: could not find: ", template_name)
            return None

        full_path = os.path.dirname(os.path.abspath(fname))

        # Add (if needed) template dir inside the sys.path
        # This is because a template is actually a Python class
        template_path = os.path.dirname(full_path)
        if template_path not in sys.path:
            sys.path.append(os.path.join(template_path))
            sys.path.append(os.path.join(template_path, template_name))

        # mod = imp.load_source("mod_%s" % template_name, fname)
        # mod = importlib.import_module("template")

        # import importlib.util

        spec = importlib.util.spec_from_file_location(f"mod_{template_name}", fname)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        self.template = mod.Template()

    def code(self, outdir):
        for m in self.modules:
            self.template.code(m, self, outdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a flow file to Code using a template"
    )
    parser.add_argument("flow", nargs="?", help="Flow file to convert")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-t", "--template", help="Template file")
    parser.add_argument("--strict", action="store_true", help="Strict mode")
    parser.add_argument(
        "--templates", action="store_true", help="List available template names"
    )
    parser.add_argument(
        "--templates-dir", action="append", default=[], help="Additional directory to search for templates"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + VERSION
    )

    args = parser.parse_args()

    if args.templates:
        search_dirs = [os.path.join(APP_PATH, "templates")] + args.templates_dir
        templates = set()
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for name in os.listdir(s_dir):
                    if os.path.isdir(os.path.join(s_dir, name)) and os.path.exists(os.path.join(s_dir, name, "template.py")):
                        templates.add(name)
        for t in sorted(list(templates)):
            print(t)
        sys.exit(0)

    if not args.flow:
        parser.error("the following arguments are required: flow")

    f2c = Flow2Code(args.flow, args.template, args.strict, args.templates_dir)
    res = f2c.code(args.output)
