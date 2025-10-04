#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from texts import texts as TEMPL


# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================

def _get_method_template(method: str) -> str:
	"""Get the appropriate template based on HTTP method"""
	method_upper = method.upper()
	template_map = {
		"GET": "ENDPOINT_GET",
		"POST": "ENDPOINT_POST",
		"PUT": "ENDPOINT_PUT",
		"PATCH": "ENDPOINT_PATCH",
		"DELETE": "ENDPOINT_DELETE",
	}
	return template_map.get(method_upper, "ENDPOINT_POST")


# ==================================================================================================
# CLASS METHODS
# ==================================================================================================

def generate_file_index(self, mod: Module, output: str):
	"""Generate the index.ts file for Cloudflare Workers"""
	mod_name = self.mod_name(mod)

	# create the output directory
	outfile = os.path.join(output, "src", "index.ts")
	out = self.create_file(outfile, mod)

	# Prepare methods list for import
	methods = []
	for ep in mod.endpoints.values():
		method_name = self.endpoint_mk_function(ep)
		methods.append(method_name)

	# Sort methods
	methods.sort()

	# Determine permissions constant name
	permissions_const = f"{mod_name.upper()}_PERMISSIONS"

	# Prepare snippets
	snippets = {
		"__methods": ", ".join(methods),
		"__mod_name": mod_name,
		"__permissions_const": permissions_const,
	}

	# Write the file header
	out.write(TEMPL["INDEX_FILE_START"] % snippets)

	# Write each endpoint
	for ep in mod.endpoints.values():
		_write_endpoint(self, ep, out, mod)

	# Write the file footer
	out.write(TEMPL["INDEX_FILE_END"] % snippets)

	# close the output file
	out.close()
	print("Generated", outfile)


def _write_endpoint(self, ep: Endpoint, out, mod: Module):
	"""Write a single endpoint to the index.ts file"""
	method_name = self.endpoint_mk_function(ep)
	method_upper = ep.method.upper()

	# Determine parameter handling based on method
	if method_upper == "GET":
		param_source = "query"
		param_name = "query"
	else:
		# For POST, PUT, PATCH, DELETE - use body
		param_source = "data"
		param_name = "data"

	# Build the endpoint dictionary
	dct = {
		"__path": f"/api{ep.path}",
		"__method_name": method_name,
		"__param_source": param_source,
		"__param_name": param_name,
	}

	# Get the appropriate template
	template_key = _get_method_template(ep.method)

	# Write the endpoint code
	out.write(TEMPL[template_key] % dct)
