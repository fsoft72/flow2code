#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from texts import texts as TEMPL


# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================

def _create_function_name(ep: Endpoint) -> str:
	"""Create function name from endpoint, e.g., POST /tags/add -> tag_add"""
	# Remove leading /api if present
	path = ep.path.replace("/api/", "/").replace("/api", "")
	# Remove leading slash
	path = path.lstrip("/")
	# Replace slashes with underscores and remove path params
	parts = []
	for part in path.split("/"):
		if not part.startswith(":"):
			# Replace hyphens with underscores for valid function names
			parts.append(part.replace("-", "_"))

	return "_".join(parts)


def _get_method_template(method: str, has_params: bool) -> str:
	"""Get the appropriate template based on HTTP method and parameter presence"""
	method_upper = method.upper()
	suffix = "" if has_params else "_NO_PARAMS"
	template_map = {
		"GET": f"ENDPOINT_GET{suffix}",
		"POST": f"ENDPOINT_POST{suffix}",
		"PUT": f"ENDPOINT_PUT{suffix}",
		"PATCH": f"ENDPOINT_PATCH{suffix}",
		"DELETE": f"ENDPOINT_DELETE{suffix}",
	}
	return template_map.get(method_upper, f"ENDPOINT_POST{suffix}")


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
		method_name = _create_function_name(ep)
		methods.append(method_name)

	# Sort methods
	methods.sort()

	# Format methods import with newlines every 4 methods
	formatted_methods = []
	for i, method in enumerate(methods):
		if i > 0 and i % 4 == 0:
			formatted_methods.append("\n\t")
		formatted_methods.append(method)
		if i < len(methods) - 1:
			formatted_methods.append(", ")

	# Determine permissions constant name
	permissions_const = f"{mod_name.upper()}_PERMISSIONS"

	# Prepare snippets
	snippets = {
		"__methods": "".join(formatted_methods),
		"__mod_name": mod_name,
		"__permissions_const": permissions_const,
		"__module_snippet": self.snippets.get("_module", ""),
		"__module_init_snippet": self.snippets.get("module_init", ""),
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
	method_name = _create_function_name(ep)
	method_upper = ep.method.upper()

	# Check if endpoint has parameters
	has_params = len(ep.parameters) > 0

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
	template_key = _get_method_template(ep.method, has_params)

	# Write the endpoint code
	out.write(TEMPL[template_key] % dct)
