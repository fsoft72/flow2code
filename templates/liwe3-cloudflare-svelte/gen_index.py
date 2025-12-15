#!/usr/bin/env python3

import os
from lib.types import Module


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================


def generate_file_index(self, mod: Module, output: str):
    """Generate the index.ts file that exports everything from types.ts and actions.ts"""
    mod_name = self.mod_name(mod)

    # Check if we have types or endpoints to export
    has_types = mod.types and len(mod.types) > 0
    has_endpoints = mod.endpoints and len(mod.endpoints) > 0

    # If nothing to export, skip
    if not has_types and not has_endpoints:
        print(f"Skipping index generation - no types or endpoints found")
        return

    # Create the src directory if it doesn't exist
    src_dir = os.path.join(output, "src")
    os.makedirs(src_dir, exist_ok=True)

    # Create the output file
    outfile = os.path.join(src_dir, "index.ts")
    out = self.create_file(outfile, mod)

    # Export from types.ts if types exist
    if has_types:
        out.write("export * from './types';\n")

    # Export from actions.ts if endpoints exist
    if has_endpoints:
        out.write("export * from './actions';\n")

    # Close the output file
    out.close()
    print(f"Generated {outfile}")
