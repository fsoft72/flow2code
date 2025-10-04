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

	# Write each permission
	for perm in mod.permissions.values():
		# Escape single quotes in the description
		description = perm.description.replace("'", "\\'")
		out.write(
			TEMPL["PERMS_ROW"] % {"name": perm.name, "description": description}
		)

	# Write the file footer
	out.write(TEMPL["PERMS_FILE_END"] % snippets)

	# close the output file
	out.close()

	print("Generated", outfile)
