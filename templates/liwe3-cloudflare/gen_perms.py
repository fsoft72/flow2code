#!/usr/bin/env python3

import os
from lib.types import Module
from texts import texts as TEMPL


# =================================================================================================
# EXPORTED FUNCTIONS
# =================================================================================================
def generate_file_perms(self, mod: Module, output: str):
    """
    Generate the perms.ts file
    """
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "src", "perms.ts")
    out = self.create_file(outfile, mod)

    # Determine permissions constant name
    permissions_const = f"{mod_name.upper()}_PERMISSIONS"

    # Prepare snippets for the template
    snippets = {
        "__mod_name": mod_name,
        "__mod_name_camel": mod_name.capitalize(),
        "__permissions_const": permissions_const,
    }

    # Write the file header
    out.write(TEMPL["PERMS_FILE_START"] % snippets)

    def _const_name(perm) -> str:
        # Extract the suffix by removing the module name prefix
        # e.g., 'system.admin' -> 'admin'
        if "." in perm.name:
            suffix = perm.name.split(".", 1)[1]
        else:
            suffix = perm.name

        # Normalize suffix: replace '-' with '_' and convert to uppercase
        const_suffix = suffix.replace("-", "_").replace(".", "_").upper()
        const_name = f"{mod_name.upper()}_PERM_{const_suffix}"

        return const_name

    # Generate permission constants
    out.write(TEMPL["PERMS_CONSTANTS_START"])
    for perm in mod.permissions.values():
        const_name = _const_name(perm)

        out.write(
            TEMPL["PERMS_CONST_ROW"]
            % {"const_name": const_name, "perm_name": perm.name}
        )
    out.write(TEMPL["PERMS_CONSTANTS_END"])

    # Start the permissions array
    out.write(TEMPL["PERMS_ARRAY_START"] % snippets)

    # Write each permission
    for perm in mod.permissions.values():
        # Escape single quotes in the description
        description = perm.description.replace("'", "\\'")
        out.write(
            TEMPL["PERMS_ROW"] % {"name": _const_name(perm), "description": description}
        )

    # Write the file footer
    out.write(TEMPL["PERMS_FILE_END"] % snippets)

    # close the output file
    out.close()

    print("Generated", outfile)
