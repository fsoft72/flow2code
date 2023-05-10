#!/usr/bin/env python3

import os
from lib.types import Module, Type
from lib.utils import camel2snake
from texts import texts as TEMPL
from collections import defaultdict

# =================================================================================================
# INTERNAL FUNCTIONS
# =================================================================================================


# =================================================================================================
# EXPORTED FUNCTIONS
# =================================================================================================
def generate_file_types(self, mod: Module, output: str):
    """
    generate all the types dart files
    """

    def _gen_type(typ: Type):
        fname = camel2snake(typ.name)
        outfile = os.path.join(output, "lib", "models", mod_name, fname + ".dart")
        out = self.create_file(outfile, mod)
        out.write(TEMPL["TYPE_FILE_START"] % self.snippets)

        dct = defaultdict(lambda: "", self.snippets)
        dct["name"] = typ.name

        # here we save all params to create the constructor
        params = []

        out.write(TEMPL["INTERFACE_START"] % dct)
        for f in typ.fields:
            if f.description == "":
                out.write(self.prepare_field(f, TEMPL["INTERFACE_PARAM_NO_DESCR"], ""))
            else:
                out.write(self.prepare_field(f, TEMPL["INTERFACE_PARAM"], ""))

            if f.required:
                params.append(TEMPL["PARAM_REQUIRED"] % {"name": f.name})
            else:
                params.append(TEMPL["PARAM_OPTIONAL"] % {"name": f.name})

        dct["_constructor_params"] = ",\n      ".join(params)
        dct.update(self.snippets)

        # create the constructor
        out.write(TEMPL["CONSTRUCTOR"] % dct)

        out.write(TEMPL["INTERFACE_END"])

        out.write(TEMPL["TYPE_FILE_END"] % self.snippets)
        # close the output file
        out.close()

        print("Generated", outfile)

    mod_name = self.mod_name(mod)

    for ep in mod.types.values():
        _gen_type(ep)
