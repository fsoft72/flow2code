#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint, Field
from lib.const import FieldType
from texts import texts as TEMPL


# ==================================================================================================
# HELPER FUNCTIONS
# ==================================================================================================

def _get_zod_type(field: Field, mod: Module = None) -> str:
	"""
	Maps Field to Zod schema type string.
	"""
	field_type = field.type[0]

	# Base type mapping
	if field_type == FieldType.STR:
		base = "z.string()"
	elif field_type == FieldType.NUMBER:
		base = "z.coerce.number()"
	elif field_type == FieldType.FLOAT:
		base = "z.coerce.number()"
	elif field_type == FieldType.BOOL:
		base = "z.coerce.boolean()"
	elif field_type == FieldType.DATE:
		base = "z.string()"
	elif field_type == FieldType.DATETIME:
		base = "z.coerce.date()"
	elif field_type == FieldType.FILE:
		base = "z.any()"
	elif field_type == FieldType.OBJECT:
		base = "z.any()"
	elif field_type == FieldType.CUSTOM:
		# Custom types (enums, other types, etc.)
		if len(field.type) > 1:
			custom_type = field.type[1]
			if custom_type == "datetime":
				base = "z.coerce.date()"
			else:
				# Look up the actual type/enum name
				if mod and custom_type in mod.flow.types:
					type_name = mod.flow.types[custom_type].name
					base = f"Z{type_name}"
				elif mod and custom_type in mod.flow.enums:
					enum_name = mod.flow.enums[custom_type].name
					base = f"Z{enum_name}"
				else:
					# Fallback to custom type ID
					base = f"Z{custom_type}"
		else:
			base = "z.any()"
	else:
		base = "z.any()"

	# Add validation constraints for strings
	if field_type == FieldType.STR and field.min_length and field.min_length > 0:
		base += f".min( {field.min_length}, '{field.name.capitalize()} is required' )"

	if field_type == FieldType.STR and field.size and field.size > 0:
		base += f".max( {field.size} )"

	# Handle arrays
	if field.is_array:
		if base.startswith("Z"):
			base = f"z.array( {base} )"
		else:
			base += ".array()"

	# Handle optional fields
	if not field.required:
		base += ".optional()"

	# Handle defaults
	if field.default:
		if field_type == FieldType.STR:
			base += f".default( '{field.default}' )"
		else:
			base += f".default( {field.default} )"

	return base


def _create_file_name(ep: Endpoint, mod: Module) -> str:
	"""Create file name from endpoint path, e.g., /tags/add -> tag-add.ts"""
	# Remove leading /api if present
	path = ep.path.replace("/api/", "/").replace("/api", "")
	# Remove leading slash
	path = path.lstrip("/")
	# Replace slashes with dashes and remove path params
	parts = []
	for part in path.split("/"):
		if not part.startswith(":"):
			parts.append(part)

	return "-".join(parts) + ".ts"


def _create_function_name(ep: Endpoint, mod: Module) -> str:
	"""Create function name from endpoint, e.g., POST /tags/add -> tag_add"""
	# Remove leading /api if present
	path = ep.path.replace("/api/", "/").replace("/api", "")
	# Remove leading slash
	path = path.lstrip("/")
	# Replace slashes with underscores and remove path params
	parts = []
	for part in path.split("/"):
		if not part.startswith(":"):
			parts.append(part)

	return "_".join(parts)


def _pascal_case(text: str) -> str:
	"""Convert text to PascalCase"""
	return "".join(word.capitalize() for word in text.replace("-", "_").split("_"))


def _format_param_docs(ep: Endpoint) -> str:
	"""Format parameter documentation for JSDoc"""
	if not ep.parameters:
		return " * @param {LiWEApp} app - The LiWE application instance with database access\n"

	lines = [" * @param {LiWEApp} app - The LiWE application instance with database access"]

	# Get the params type name
	func_name = _create_function_name(ep, None)
	params_type = _pascal_case(func_name) + "Params"

	lines.append(f" * @param {{{params_type}}} params - Request parameters")

	for param in ep.parameters:
		opt = "" if param.required else "?"
		type_str = "string"  # Simplified for docs

		if param.type[0] == FieldType.NUMBER or param.type[0] == FieldType.FLOAT:
			type_str = "number"
		elif param.type[0] == FieldType.BOOL:
			type_str = "boolean"

		if param.is_array:
			type_str += "[]"

		descr = param.description if param.description else f"{param.name} parameter"
		lines.append(f" * @param {{{type_str}}} {opt}params.{param.name} - {descr}")

	return "\n".join(lines) + "\n"


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================

def generate_file_methods(self, mod: Module, output: str):
	"""Generate individual method files in src/methods/ directory"""
	mod_name = self.mod_name(mod)

	# Create methods directory
	methods_dir = os.path.join(output, "src", "methods")
	os.makedirs(methods_dir, exist_ok=True)

	# Generate utils.ts file
	_generate_utils_file(self, mod, methods_dir)

	# Generate each endpoint method file
	for ep in mod.endpoints.values():
		_generate_method_file(self, ep, mod, methods_dir)

	# Generate index.ts that re-exports all methods
	_generate_methods_index(self, mod, methods_dir)

	# Generate methods.ts wrapper in src/
	_generate_methods_wrapper(self, mod, output)


def _generate_utils_file(self, mod: Module, methods_dir: str):
	"""Generate the utils.ts file with common imports"""
	mod_name = self.mod_name(mod)
	outfile = os.path.join(methods_dir, "utils.ts")

	with open(outfile, "w") as out:
		out.write(TEMPL["METHOD_UTILS_FILE"] % {"__mod_name": mod_name})

	print(f"Generated {outfile}")


def _generate_method_file(self, ep: Endpoint, mod: Module, methods_dir: str):
	"""Generate a single method file for an endpoint"""
	mod_name = self.mod_name(mod)
	file_name = _create_file_name(ep, mod)
	func_name = _create_function_name(ep, mod)
	outfile = os.path.join(methods_dir, file_name)

	# Store module reference in endpoint for type lookups
	ep.mod = mod

	# Extract snippets from existing file if it exists
	out = self.create_file(outfile, mod)

	# Determine names
	schema_name = _pascal_case(func_name) + "Schema"
	params_type = _pascal_case(func_name) + "Params"
	result_type = _pascal_case(func_name) + "Result"

	# Get snippet for headers block
	headers_block_name = func_name + "_headers"
	headers_snippet = self.snippets.get(headers_block_name, "\n// Custom imports here\n")

	# Get snippet for function body
	body_block_name = func_name
	body_snippet = self.snippets.get(body_block_name, "\n\t// Your code here\n")

	# File start
	description = ep.description if ep.description else ep.short_descr if ep.short_descr else f"{func_name} endpoint"
	out.write(TEMPL["METHOD_FILE_START"] % {"__endpoint_description": description})

	# Generate schema if there are parameters
	if ep.parameters:
		_write_schema(out, ep, schema_name, func_name)
		_write_params_type(out, params_type, schema_name, func_name)

	# Generate result type
	_write_result_type(out, ep, result_type, func_name)

	# Write headers block
	out.write(TEMPL["METHOD_HEADERS_BLOCK"] % {
		"__block_name": headers_block_name,
		"__snippet": headers_snippet
	})

	# Write function start
	param_docs = _format_param_docs(ep)
	params_arg = f", params: {params_type}" if ep.parameters else ""

	out.write(TEMPL["METHOD_FUNCTION_START"] % {
		"__function_description": description,
		"__param_docs": param_docs,
		"__function_name": func_name,
		"__params_arg": params_arg,
		"__result_type": result_type
	})

	# Write validation if params exist
	if ep.parameters:
		out.write(TEMPL["METHOD_VALIDATION"] % {"__schema_name": schema_name})

		# Extract param names
		param_names = ", ".join([p.name for p in ep.parameters])
		out.write(TEMPL["METHOD_PARAMS_EXTRACT"] % {"__param_names": param_names})

	# Write function body block
	out.write(TEMPL["METHOD_BODY_BLOCK"] % {
		"__block_name": body_block_name,
		"__snippet": body_snippet
	})

	# Write function end
	out.write(TEMPL["METHOD_FUNCTION_END"])

	out.close()
	print(f"Generated {outfile}")


def _write_schema(out, ep: Endpoint, schema_name: str, func_name: str):
	"""Write the Zod schema definition"""
	# Build schema properties documentation
	properties = []
	for param in ep.parameters:
		opt = "[" if not param.required else ""
		opt_end = "]" if not param.required else ""
		type_str = "string"

		if param.type[0] == FieldType.NUMBER or param.type[0] == FieldType.FLOAT:
			type_str = "number"
		elif param.type[0] == FieldType.BOOL:
			type_str = "boolean"

		if param.is_array:
			type_str += "[]"

		descr = param.description if param.description else f"{param.name} parameter"
		constraints = []
		if param.required:
			constraints.append("required")
		if param.min_length and param.min_length > 0:
			constraints.append(f"min {param.min_length}")
		if param.size and param.size > 0:
			constraints.append(f"max {param.size}")

		constraint_str = f" ({', '.join(constraints)})" if constraints else ""

		properties.append(f" * @property {{{opt}{type_str}{opt_end}}} {param.name} - {descr}{constraint_str}")

	schema_description = ep.description if ep.description else f"{func_name} parameters"

	out.write(TEMPL["METHOD_SCHEMA_START"] % {
		"__schema_description": schema_description,
		"__schema_properties": "\n".join(properties),
		"__schema_name": schema_name
	})

	# Write schema fields
	for param in ep.parameters:
		zod_type = _get_zod_type(param, ep.mod if hasattr(ep, 'mod') else None)
		out.write(TEMPL["METHOD_SCHEMA_FIELD"] % {
			"name": param.name,
			"zod_type": zod_type
		})

	out.write(TEMPL["METHOD_SCHEMA_END"])


def _write_params_type(out, params_type: str, schema_name: str, func_name: str):
	"""Write the TypeScript params type"""
	out.write(TEMPL["METHOD_PARAMS_TYPE"] % {
		"__function_description": func_name,
		"__params_type": params_type,
		"__schema_name": schema_name
	})


def _write_result_type(out, ep: Endpoint, result_type: str, func_name: str):
	"""Write the TypeScript result type"""
	# For now, create a simple result type
	# TODO: Properly parse return type from endpoint
	result_fields = "data: any"

	out.write(TEMPL["METHOD_RESULT_TYPE"] % {
		"__function_description": func_name,
		"__result_type": result_type,
		"__result_fields": result_fields
	})


def _generate_methods_index(self, mod: Module, methods_dir: str):
	"""Generate the methods/index.ts file that re-exports all methods"""
	mod_name = self.mod_name(mod)
	outfile = os.path.join(methods_dir, "index.ts")

	with open(outfile, "w") as out:
		out.write(TEMPL["METHODS_INDEX_START"] % {"__mod_name": mod_name})

		for ep in mod.endpoints.values():
			file_name = _create_file_name(ep, mod).replace(".ts", "")
			func_name = _create_function_name(ep, mod)
			params_type = _pascal_case(func_name) + "Params"
			result_type = _pascal_case(func_name) + "Result"

			# Only export params type if there are parameters
			if ep.parameters:
				out.write(TEMPL["METHODS_INDEX_EXPORT"] % {
					"__function_name": func_name,
					"__params_type": params_type,
					"__result_type": result_type,
					"__file_name": file_name
				})
			else:
				# For endpoints without params, only export function and result type
				out.write(f"export {{ {func_name}, type {result_type} }} from './{file_name}';\n")

	print(f"Generated {outfile}")


def _generate_methods_wrapper(self, mod: Module, output: str):
	"""Generate the src/methods.ts wrapper file that re-exports from methods/index.ts"""
	mod_name = self.mod_name(mod)
	outfile = os.path.join(output, "src", "methods.ts")

	with open(outfile, "w") as out:
		out.write(TEMPL["METHODS_WRAPPER_FILE"] % {
			"__mod_name": mod_name,
			"__mod_name_camel": mod_name.capitalize()
		})

	print(f"Generated {outfile}")
