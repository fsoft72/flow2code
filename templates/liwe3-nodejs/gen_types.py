#!/usr/bin/env python3

import os
from lib.types import Module, Type, Enum
from texts import texts as TEMPL

# =================================================================================================
# INTERNAL FUNCTIONS
# =================================================================================================


def _gen_enum(fout, enum: Enum):
    keys = sorted(list(enum.consts.keys()))

    dct = {"name": enum.name, "description": enum.description}

    if dct["description"]:
        dct["description"] = " - " + dct["description"]

    fout.write(TEMPL["ENUM_START"] % dct)
    for k in keys:
        v = enum.consts[k]
        d = {"name": k, "val": v["name"], "description": v["description"]}
        fout.write(TEMPL["ENUM_ROW"] % d)

    fout.write(TEMPL["ENUM_END"] % dct)

    fout.write(TEMPL["ENUM_OBJ_START"] % dct)
    for k in keys:
        v = enum.consts[k]
        d = {"name": k, "val": v["name"]}
        fout.write(TEMPL["ENUM_OBJ_ROW"] % d)

    fout.write(TEMPL["ENUM_OBJ_END"] % dct)


# =================================================================================================
# EXPORTED FUNCTIONS
# =================================================================================================
def generate_file_types(self, mod: Module, output: str):
    """
    generate the methods.ts file
    """
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "server", "modules", mod_name, "types.ts")
    out = self.create_file(outfile, mod)

    out.write(TEMPL["TYPES_FILE_START"] % self.snippets)

    for ep in mod.enums.values():
        _gen_enum(out, ep)

    for ep in mod.types.values():
        self._gen_type(out, ep)

    out.write(TEMPL["TYPES_FILE_END"] % self.snippets)
    # close the output file
    out.close()

    print("Generated", outfile)


def _gen_type(self, fout, typ: Type):
    dct = {"name": typ.name}

    fout.write(TEMPL["INTERFACE_START"] % dct)
    for f in typ.fields:
        fout.write(self.prepare_field(f, TEMPL["INTERFACE_PARAM"], ""))
    fout.write(TEMPL["INTERFACE_END"])

    fout.write(TEMPL["INTERFACE_KEYS_START"] % dct)
    for f in typ.fields:
        fout.write(self.prepare_field(f, TEMPL["INTERFACE_KEY_PARAM"], ""))
    fout.write(TEMPL["INTERFACE_KEYS_END"])
