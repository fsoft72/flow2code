#!/usr/bin/env python3

import re
import os
from collections import defaultdict

from .const import FieldType
from .types import Module, Endpoint, Function, Field
from .utils import type2typescript

# RegExp that extracts the name from d2r_start block_name and d2r_end block_name
re_block_name = re.compile(r".*(d2r|f2c)_(start|end)\s+(?P<name>[a-zA-Z0-9_]+)\s*")


class TemplateBase:
    snippets = {}
    mod: Module = None

    def __init__(self):
        self.name = "Base Template"

    def __str__(self):
        return self.name

    def extract_snippets(self, mod: Module, fname: str):
        # load the whole fname in memory
        # and extracts all code contained in /* dr_start (block_name) */ and /* dr_end (block_name) */
        # using the block_name as key in the snippets dictionary
        # the code is stored in the snippets dictionary as a list of lines

        # self.mod = mod

        self.snippets = {}

        if not os.path.isfile(fname):
            return

        # open the file
        lines = open(fname, "r").readlines()

        # initialize the snippets dictionary
        self.snippets = {}

        # initialize the current block name
        block_name = None

        # initialize the current block lines
        block_lines = []

        # iterate over the lines
        for line in lines:
            # check if the line starts with dr_start
            if (line.find("f2c_start") != -1) or (line.find("d2r_start") != -1):
                g = re_block_name.match(line)
                block_name = g.group("name")
                # initialize the block lines
                block_lines = []

            # check if the line starts with dr_end
            elif (line.find("f2c_end") != -1) or (line.find("d2r_end") != -1):
                g = re_block_name.match(line)
                block_name = g.group("name")

                # store the block lines in the snippets dictionary
                self.snippets[block_name] = "".join(block_lines).rstrip()

                # initialize the block lines
                block_lines = []

            # check if the block name is not None
            elif block_name is not None:
                # append the line to the block lines
                block_lines.append(line)

        self.snippets.update(
            {
                "__name_camel": mod.name.strip(),
                "__name_lower": mod.name.lower().strip().replace(" ", "_"),
                "__name_upper": mod.name.upper().strip().replace(" ", "_"),
            }
        )

    def code(self, mod: Module, flow: any, output: str):
        """
        Empty code generation method
        """
        self.mod = mod
        self.flow = flow

    def mod_name(self, mod: Module):
        """
        Returns the module name in `snake_case`
        """
        return mod.name.lower().strip().replace(" ", "_").replace("-", "_")

    def valid_function_name(self, name: str) -> str:
        """
        Returns the passed `name` as a valid function name, stripping all the invalid characters
        """
        name = name.split(":")[0]
        name = name.replace("/", "_").replace("-", "_").lower()

        # remove all characters that are not a-z, 0-9 or _
        name = re.sub(r"[^a-z0-9_-]", "", name)
        # remove all double underscores
        name = re.sub(r"__+", "_", name)
        name = name.strip("_")
        return name

    def endpoint_mk_function(self, ep: Endpoint):
        name = f"""{ep.method}_{ep.path}"""

        return self.valid_function_name(name)

    def create_file(self, full_path: str, mod: Module, keep_all_snippets: bool = False):
        """
        This method creates a new output file
        It also creates all the missing directories and extract snippets from the file if it exists.

        @param full_path: the full path of the file to create
        @param keep_all_snippets: if True, all the snippets are kept in the snippets dictionary

        @return: the file object
        """
        # get the full path of the file
        full_path = os.path.abspath(full_path)

        # get the directory of the file
        dirname = os.path.dirname(full_path)

        # create the directory if it does not exist
        if not os.path.isdir(dirname):
            os.makedirs(dirname, exist_ok=True)

        # if we don't keep all the snippets, we clear the snippets dictionary
        if not keep_all_snippets:
            self.snippets = {}

        # check if the file exists
        if os.path.isfile(full_path):
            # extract snippets from the file
            self.extract_snippets(mod, full_path)

        # convert snippets to a defaultdict
        self.snippets = defaultdict(lambda: "", self.snippets)

        # open the file
        f = open(full_path, "w")

        # return the file object
        return f

    def prepare_field(
        self, field: Field, template, template_obj, honour_float=False, use_enums=False
    ):
        dct = {
            "name": field.name,
            "type": "any",
            "type_obj": False,
            "required": field.required,
            "private": field.private,
            "description": field.description,
            "opt": "",
            "param_default": field.default,
            "is_array": field.is_array,
            "default": field.default,
        }

        # The template param holds the default template string to be used
        # it could change if we need to use the _OBJ version of the template
        templ = template

        if dct["param_default"] is None:
            dct["param_default"] = "undefined"

        if dct["required"]:
            dct["_req"] = "true"
            dct["_is_req"] = "req"
            dct["param_default"] = ""
        else:
            dct["opt"] = "?"
            dct["_is_req"] = "opt"
            dct["_req"] = "false"

        if dct["private"]:
            dct["private"] = "true"
        else:
            dct["private"] = "false"

        _typ = field.type[0]

        if _typ == FieldType.STR:
            dct["type"] = "string"
            if dct["param_default"] and dct["param_default"] != "undefined":
                dct["param_default"] = '"%s"' % dct["param_default"]
        elif _typ == FieldType.NUMBER:
            dct["type"] = "number"
        elif _typ == FieldType.FLOAT:
            if honour_float:
                dct["type"] = "float"
            else:
                dct["type"] = "number"
        elif _typ == FieldType.BOOL:
            dct["type"] = "boolean"
        elif _typ == FieldType.DATE:
            dct["type"] = "Date"
        elif _typ == FieldType.FILE:
            dct["type"] = "File"
        elif _typ == FieldType.CUSTOM:
            typ = field.type[1]
            dct["type"] = typ
            if typ in self.mod.flow.enums:
                dct["type"] = self.mod.flow.enums[typ].name
                dct["type_obj"] = True
                if use_enums:
                    templ = template_obj
            elif typ in self.mod.flow.types:
                dct["type"] = self.mod.flow.types[typ].name
                dct["type_obj"] = True

        if dct["type"] == "iliwe":
            dct["type"] = "ILiWE"
        elif dct["type"] == "ilrequest":
            dct["type"] = "ILRequest"
        elif dct["type"] == "ilresponse":
            dct["type"] = "ILResponse"
        elif dct["type"] in ("date", "datetime"):
            dct["type"] = "Date"

        if dct["is_array"]:
            dct["type"] += "[]"

        if dct["default"]:
            if dct["type"].startswith("string"):
                dct["_default"] = ', default: "%s"' % field.default
            else:
                dct["_default"] = ", default: %s" % field.default
        else:
            dct["_default"] = ""

        if dct["param_default"]:
            dct["param_default"] = " = %s" % dct["param_default"]
            dct["opt"] = ""

        if dct["_req"] == "true":
            dct["_req_param"] = ", required: %(_req)s%(_default)s" % dct
        else:
            dct["_req_param"] = ""

        if dct["type"].startswith(("type.", "enum.")):
            dct["type"] = "any"
            if self.mod.flow.strict:
                raise Exception("Type or enum not found: %s" % dct["type"])

        return templ % dct

    def join_newlines(self, lst: list[str], num_elems: int = 5) -> str:
        # convert methods to a string, adding a new line every 5 elements
        res = ""
        for i, m in enumerate(lst):
            res += m
            if i % num_elems == (num_elems - 1):
                res += ",\n\t"
            else:
                res += ", "

        return res.rstrip()

    def mk_documentation(
        self,
        main_doc: str,
        params_doc: list[str],
        ret_name: str,
        ret_type: str,
        ret_doc: str,
        TEMPL: dict[str, str],
    ) -> str:
        if main_doc:
            description = (
                [x for x in main_doc.split("\n") if x.strip()] + [""] + params_doc
            )
        else:
            description = params_doc

        ret_descr = ret_doc
        if ret_descr:
            ret_descr = " - " + ret_descr
        else:
            ret_descr = ""

        description.append("")
        description.append(
            TEMPL["EP_DOC_RETURN"]
            % {
                "doc": ret_descr,
                "name": ret_name,
                "type": ret_type,
                "return_type": type2typescript(ret_type, self.mod.flow),
            }
        )

        description = (
            " *"
            + "\n *".join([" " + d if len(d) else "" for d in description])
            + "\n *"
        )

        return description

    def params_and_doc(
        self, fn: Endpoint | Function, TEMPL: dict[str, str], honour_float: bool = True
    ) -> tuple[list[str], list[str]]:
        params = []
        doc = []
        for p in fn.parameters:
            if p.type == FieldType.FILE:
                continue
            params.append(
                self.prepare_field(
                    p,
                    TEMPL["EP_TYPED_PARAM"],
                    "",
                    honour_float=honour_float,
                    use_enums=True,
                )
            )
            dct = {
                "name": p.name,
                "doc": p.description,
                "_is_req": "req" if p.required else "opt",
            }
            doc.append(TEMPL["EP_DOC_FIELD"] % dct)

        if params:
            params = ", ".join(params) + ", "
        else:
            params = ""

        documentation = self.mk_documentation(
            fn.description,
            doc,
            fn.return_name,
            fn.return_type,
            "",  # fn.return_description,
            TEMPL,
        )

        return [params, documentation]
