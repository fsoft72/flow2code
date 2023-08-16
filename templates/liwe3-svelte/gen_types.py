#!/usr/bin/env python3

import os
from lib.types import Module, Enum, Type
from texts import texts as TEMPL


# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================
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


# ==================================================================================================
# CLASS METHODS
# ==================================================================================================
def generate_file_types(self, mod: Module, output: str):
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "src", "modules", mod_name, "types.ts")
    fout = self.create_file(outfile, mod)

    fout.write(TEMPL["TYPES_START"] % self.snippets)

    for ep in mod.enums.values():
        _gen_enum(fout, ep)

    for typ in mod.types.values():
        self._gen_type(fout, typ)

    # close the output file
    fout.close()
    print("Generated", outfile)


def _gen_type(self, fout, typ: Type):
    dct = {"name": typ.name}

    fout.write(TEMPL["INTERFACE_START"] % dct)
    for f in typ.fields:
        fout.write(self.prepare_field(f, TEMPL["INTERFACE_PARAM"], ""))
    fout.write(TEMPL["INTERFACE_END"])
