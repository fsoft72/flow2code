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
import imp

# append the path of this file in the python path
APP_PATH = os.path.dirname(os.path.realpath(__file__))

from lib.types import Module, Permission, Endpoint, Type, Enum, Function

VERSION = "0.3.0"


class Flow2Code:
    # List of modules to be converted
    modules: list[Module] = []

    # Global variables
    permissions: dict[str, Permission] = {}
    endpoints: dict[str, Endpoint] = {}
    types: dict[str, Type] = {}
    enums: dict[str, Enum] = {}
    functions: dict[str, Function] = {}

    # The template module instance
    template = None

    strict: bool = False

    def __init__(self, flow, template, strict):
        self.strict = strict

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

        fname = os.path.join(APP_PATH, "templates", template_name, "template.py")

        if not os.path.exists(fname):
            print("ERROR: could not find: ", fname)
            return None

        full_path = os.path.dirname(os.path.abspath(fname))

        # Add (if needed) template dir inside the sys.path
        # This is because a template is actually a Python class
        template_path = os.path.dirname(full_path)
        if template_path not in sys.path:
            sys.path.append(os.path.join(template_path))
            sys.path.append(os.path.join(template_path, template_name))

        mod = imp.load_source("mod_%s" % template_name, fname)
        self.template = mod.Template()

    def code(self, outdir):
        for m in self.modules:
            self.template.code(m, self, outdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a flow file to Code using a template"
    )
    parser.add_argument("flow", help="Flow file to convert")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-t", "--template", help="Template file")
    parser.add_argument("--strict", action="store_true", help="Strict mode")
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + VERSION
    )

    args = parser.parse_args()

    f2c = Flow2Code(args.flow, args.template, args.strict)
    res = f2c.code(args.output)
