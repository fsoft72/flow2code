#!/usr/bin/env python3

import os
from lib.types import Module, Type, Enum
from texts import texts as TEMPL


# =================================================================================================
# EXPORTED FUNCTIONS
# =================================================================================================
def generate_file_perms(self, mod: Module, output: str):
    """
    generate the methods.ts file
    """
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "server", "modules", mod_name, "perms.ts")
    out = self.create_file(outfile, mod)

    out.write(TEMPL["PERMS_FILE_START"] % self.snippets)

    print(mod.permissions.values())

    for perm in mod.permissions.values():
        out.write(
            TEMPL["PERMS_ROW"] % {"name": perm.name, "description": perm.description}
        )

    out.write(TEMPL["PERMS_FILE_END"] % self.snippets)
    # close the output file
    out.close()

    print("Generated", outfile)
