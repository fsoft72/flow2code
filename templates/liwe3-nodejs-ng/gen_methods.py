#!/usr/bin/env python3

import os
from lib.const import FieldType
from lib.types import Module, Endpoint, Function
from lib.utils import type2typescript
from texts import texts as TEMPL

# =================================================================================================
# INTERNAL FUNCTIONS
# =================================================================================================


def _gen_db_init(mod: Module, TEMPL: dict[str, str]):
    res = [
        "\t\t_liwe = liwe;\n",
        "system_permissions_register( '%s', _module_perms );\n" % mod.name.lower(),
    ]

    DB_INDEX = TEMPL["DB_INDEX"]

    for k, v in mod.types.items():
        coll = []
        if not v.coll_table:
            continue

        for f in v.fields:
            idx = ""
            if f.idx_unique:
                idx = DB_INDEX % (
                    {"_unique": "true", "_name": f.name, "_type": "persistent"}
                )
            elif f.idx_multi:
                idx = DB_INDEX % (
                    {"_unique": "false", "_name": f.name, "_type": "persistent"}
                )
            elif f.idx_array:
                idx = DB_INDEX % (
                    {"_unique": "false", "_name": f.name + "[*]", "_type": "persistent"}
                )
            elif f.idx_fulltext:
                idx = DB_INDEX % (
                    {"_unique": "false", "_name": f.name, "_type": "fulltext"}
                )

            if not idx:
                continue

            coll.append(idx)

        if coll:
            dct = {
                "coll_name": "_coll_%s" % v.coll_table,
                "table_name": "COLL_" + v.coll_table.upper(),
                "rows": "\n\t\t\t".join(coll),
            }

            if v.coll_drop:
                dct["coll_drop"] = "{ drop: true }"
            else:
                dct["coll_drop"] = "{ drop: false }"

            res.append(TEMPL["COLL_DEF"] % dct)

    return "\n\t\t".join(res) + "\n"


# =================================================================================================
# METHODS
# =================================================================================================
def _clean_functions(self, mod: Module, mod_name: str):
    # check if inside functions there is a function called "db_init"
    # if so, delete it
    for fn in mod.functions.values():
        if fn.name.endswith("db_init"):
            mod.functions.pop(fn.id)
            break

    # creates the db_init function
    fn = Function(
        dict(
            id="db_init",
            name="%s_db_init" % mod_name,
            description="Initializes the module's database",
            parameters=[
                {
                    "id": "liwe",
                    "name": "liwe",
                    "type": "iliwe",
                    "description": "The Liwe object",
                    "required": True,
                }
            ],
            return_name="",
            returnType="bool",
            return_description="",
        ),
        mod,
    )

    mod.functions[fn.id] = fn


def generate_file_methods(self, mod: Module, output: str):
    """
    generate the methods.ts file
    """
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "server", "modules", mod_name, "methods.ts")
    out = self.create_file(outfile, mod)

    k = self.types_and_enums_list(mod)
    self.snippets["__interfaces"] = self.join_newlines(k)
    self.snippets["__import_system_perms_register"] = (
        "import { system_permissions_register } from '../system/methods';\n"
    )

    if mod.name.lower() == "system":
        self.snippets["__import_system_perms_register"] = "\n"

    # res = []
    res2 = []

    for typ in mod.types.values():
        if typ.coll_table:
            # res.append(TEMPL["TYPE_COLL_VAR"] % typ.coll_table)
            res2.append(
                TEMPL["TYPE_COLL_CONST"] % (typ.coll_table.upper(), typ.coll_table)
            )

    # self.snippets["__collections"] = "\n".join(res) + "\n\n" + "\n".join(res2)
    self.snippets["__collections"] = "\n".join(res2)

    # write the header
    out.write(TEMPL["METHODS_FILE_START"] % self.snippets)

    for ep in mod.endpoints.values():
        self._generate_endpoint(out, ep)

    self._clean_functions(mod, mod_name)

    for fn in mod.functions.values():
        self._generate_function(out, fn, mod)

    out.write(TEMPL["METHODS_FILE_END"] % self.snippets)

    # close the output file
    out.close()

    print("Generated", outfile)


def _generate_endpoint(self, fout, ep: Endpoint):
    name = self.endpoint_mk_function(ep)

    params = []
    doc = []
    for p in ep.parameters:
        if p.type == FieldType.FILE:
            continue
        params.append(
            self.prepare_field(
                p,
                TEMPL["EP_TYPED_PARAM"],
                TEMPL["EP_TYPED_PARAM"],
                honour_float=False,
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
        params = ", ".join(params)
    else:
        params = ""

    documentation = self.mk_documentation(
        ep.description,
        doc,
        ep.return_name,
        ep.return_type,
        "",  # ep.return_description,
        TEMPL,
    )

    dct = {
        "endpoint_name": name,
        "__description": documentation,
        "return_type": type2typescript(ep.return_type, self.mod.flow),
        "__parameters": params,
        "__snippet": self.snippets[name],
    }

    if ep.is_array:
        dct["return_type"] += "[]"

    fout.write(TEMPL["FOLDING_EP_START"] % dct)
    fout.write(TEMPL["EP_START"] % dct)
    fout.write(TEMPL["EP_END"] % dct)
    fout.write(TEMPL["FOLDING_END"] % dct)


def _generate_function(self, fout, fn: Function, mod: Module):
    name = fn.name

    params = []
    doc = []
    for p in fn.parameters:
        if p.type == FieldType.FILE:
            continue
        params.append(
            self.prepare_field(
                p, TEMPL["EP_TYPED_PARAM"], "", honour_float=True, use_enums=True
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

    params, documentation = self.params_and_doc(fn, TEMPL)

    dct = {
        "function_name": name,
        "__description": documentation,
        "return_type": type2typescript(fn.return_type, self.mod.flow),
        "__parameters": params,
        "__snippet": self.snippets[name],
        "__pre_snip": "",
    }

    if fn.is_array:
        dct["return_type"] += "[]"

    if name.endswith("_db_init"):
        dct["__pre_snip"] = _gen_db_init(mod, TEMPL)

    fout.write(TEMPL["FOLDING_FN_START"] % dct)
    fout.write(TEMPL["FUNCTION_START"] % dct)
    fout.write(TEMPL["FUNCTION_END"] % dct)
    fout.write(TEMPL["FOLDING_END"] % dct)
