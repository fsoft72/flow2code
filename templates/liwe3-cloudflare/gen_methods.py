#!/usr/bin/env python3

import os

from texts import texts as TEMPL

from lib.const import FieldType
from lib.types import Endpoint, Field, Module

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
        base = """z.preprocess( ( val : any ) => {
		if ( !val ) return val;
		val = val.toString().toLowerCase();
		if ( val === 'true' || val === '1' ) return true;
		if ( val === 'false' || val === '0' ) return false;
		return val;
	}, z.boolean() )"""
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
            # Replace hyphens with underscores for valid function names
            parts.append(part.replace("-", "_"))

    return "_".join(parts)


def _pascal_case(text: str) -> str:
    """Convert text to PascalCase"""
    return "".join(word.capitalize() for word in text.replace("-", "_").split("_"))


def _get_typescript_return_type(ep: Endpoint, mod: Module = None) -> str:
    """
    Maps Endpoint return_type to TypeScript type string.
    Uses inferred TypeScript types (not Zod schemas) for custom types.
    """
    if not ep.return_type:
        return "any"

    return_type = ep.return_type.lower()

    # Base type mapping
    if return_type in ["str", "string", "text"]:
        base = "string"
    elif return_type in ["int", "num", "number"]:
        base = "number"
    elif return_type in ["float", "double"]:
        base = "number"
    elif return_type in ["bool", "boolean", "check", "checkbox"]:
        base = "boolean"
    elif return_type in ["date"]:
        base = "string"
    elif return_type in ["datetime"]:
        base = "Date"
    elif return_type in ["file", "upload"]:
        base = "File"
    elif return_type in ["json", "obj", "object"]:
        base = "any"
    else:
        # Custom type - lookup in module types/enums by name
        if mod:
            # Search for type by name (not ID)
            for type_obj in mod.flow.types.values():
                if type_obj.name == ep.return_type:
                    base = type_obj.name
                    break
            else:
                # Check enums if not found in types
                for enum_obj in mod.flow.enums.values():
                    if enum_obj.name == ep.return_type:
                        base = enum_obj.name
                        break
                else:
                    # Fallback to return type as-is
                    base = ep.return_type
        else:
            base = "any"

    # Handle arrays
    if ep.is_array:
        base += "[]"

    return base


def _should_create_result_type(ep: Endpoint, mod: Module = None) -> bool:
    """
    Determines if we should create a separate Result type or use the type directly.
    Returns False for simple types and defined custom types (skip Result type creation).
    Returns True only for complex types that need a Result type wrapper.
    """
    if not ep.return_type:
        return True  # Create result type for 'any'

    return_type = ep.return_type.lower()

    # Simple/primitive types - use directly
    simple_types = [
        "str",
        "string",
        "text",
        "int",
        "num",
        "number",
        "float",
        "double",
        "bool",
        "boolean",
        "check",
        "checkbox",
        "date",
        "datetime",
        "file",
        "upload",
        "json",
        "obj",
        "object",
    ]

    if return_type in simple_types:
        return False  # Skip Result type, use simple type directly

    # Check if it's a custom type (Type or Enum)
    if mod:
        # Search for type by name
        for type_obj in mod.flow.types.values():
            if type_obj.name == ep.return_type:
                return False  # Skip Result type, use custom type directly

        # Check enums
        for enum_obj in mod.flow.enums.values():
            if enum_obj.name == ep.return_type:
                return False  # Skip Result type, use enum directly

    # For unknown types, create a Result type
    return True


def _generate_dummy_value(return_type: str) -> str:
    """
    Generates a dummy value for the given TypeScript return type.
    Used to create valid stub implementations.
    """
    # Handle array types
    if return_type.endswith("[]"):
        return "[]"

    # Handle simple types
    if return_type in ["string"]:
        return '""'
    elif return_type in ["number"]:
        return "0"
    elif return_type in ["boolean"]:
        return "false"
    elif return_type in ["Date"]:
        return "new Date()"
    elif return_type in ["any"]:
        return "null"
    else:
        # For custom types (User, GoogleTag, etc.), create an empty object with type assertion
        return f"{{}} as {return_type}"


def _is_empty_or_default_snippet(snippet: str) -> bool:
    """
    Check if the snippet is empty or contains only the default comment.
    """
    if not snippet:
        return True

    # Strip whitespace and check if it's empty or only contains the default comment
    cleaned = snippet.strip()
    return cleaned == "" or cleaned == "// Your code here"


def _format_jsdoc_description(description: str) -> str:
    """Format multiline description for JSDoc comments by prefixing each line with ' * '"""
    if not description:
        return ""

    lines = description.split("\n")
    formatted_lines = []

    for i, line in enumerate(lines):
        if i == 0:
            # First line doesn't need prefix (it's already on the same line as /**)
            formatted_lines.append(line)
        else:
            # Subsequent lines need ' * ' prefix, but no trailing space for empty lines
            if line.strip():
                formatted_lines.append(f" * {line}")
            else:
                formatted_lines.append(" *")

    return "\n".join(formatted_lines)


def _format_param_docs(ep: Endpoint) -> str:
    """Format parameter documentation for JSDoc"""
    lines = []

    # Add permissions information if present
    if ep.permissions:
        perms_str = ", ".join(ep.permissions)
        lines.append(f" * @permissions {perms_str}")
        lines.append(" *")

    if not ep.parameters:
        lines.append(
            " * @param {LiWEApp} app - The LiWE application instance with database access"
        )
        return "\n".join(lines) + "\n"

    lines.append(
        " * @param {LiWEApp} app - The LiWE application instance with database access"
    )

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

    # Extract snippets from existing file if it exists
    out = self.create_file(outfile, mod)

    # Get snippet for utils block (custom code area)
    utils_snippet = self.snippets.get(
        "utils", "\n// Add custom imports or utilities here\n"
    )

    out.write(
        TEMPL["METHOD_UTILS_FILE"]
        % {"__mod_name": mod_name, "__utils_snippet": utils_snippet}
    )

    out.close()
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
    result_type_name = _pascal_case(func_name) + "Result"

    # Get snippet for headers block
    headers_block_name = func_name + "_headers"
    headers_snippet = self.snippets.get(
        headers_block_name, "\n// Custom imports here\n"
    )

    # Get snippet for function body
    body_block_name = func_name
    body_snippet = self.snippets.get(body_block_name, "\n\t// Your code here\n")

    # File start
    description = (
        ep.description
        if ep.description
        else ep.short_descr
        if ep.short_descr
        else f"{func_name} endpoint"
    )
    formatted_description = _format_jsdoc_description(description)
    out.write(
        TEMPL["METHOD_FILE_START"] % {"__endpoint_description": formatted_description}
    )

    # Collect and write imports for referenced types
    referenced_types = _collect_referenced_types(ep, mod)
    if referenced_types:
        # Import from types.ts (assuming types are in types.ts, adjust if needed)
        types_list = ", ".join(sorted(referenced_types))
        out.write(f"import {{ {types_list} }} from '../types';\n\n")

    # Generate schema if there are parameters
    if ep.parameters:
        _write_schema(out, ep, schema_name, func_name)
        _write_params_type(out, params_type, schema_name, func_name)

    # Determine if we should create a Result type or use the type directly
    should_create_result = _should_create_result_type(ep, mod)
    actual_return_type = _get_typescript_return_type(ep, mod)

    # Generate result type only if needed
    if should_create_result:
        _write_result_type(out, ep, result_type_name, func_name)
        result_type_for_signature = result_type_name
    else:
        # Use the actual type directly
        result_type_for_signature = actual_return_type

    # Write headers block
    out.write(
        TEMPL["METHOD_HEADERS_BLOCK"]
        % {"__block_name": headers_block_name, "__snippet": headers_snippet}
    )

    # Write function start
    param_docs = _format_param_docs(ep)
    params_arg = f", params: {params_type}" if ep.parameters else ""

    out.write(
        TEMPL["METHOD_FUNCTION_START"]
        % {
            "__function_description": formatted_description,
            "__param_docs": param_docs,
            "__function_name": func_name,
            "__params_arg": params_arg,
            "__params_type": params_type,
            "__result_type": result_type_for_signature,
        }
    )

    # Write validation if params exist
    if ep.parameters:
        out.write(
            TEMPL["METHOD_VALIDATION"]
            % {"__schema_name": schema_name, "__params_type": params_type}
        )

        # Extract param names
        param_names = ", ".join([p.name for p in ep.parameters])
        out.write(TEMPL["METHOD_PARAMS_EXTRACT"] % {"__param_names": param_names})

    # Check if we need to generate a dummy implementation
    if _is_empty_or_default_snippet(body_snippet):
        # Generate dummy implementation
        dummy_value = _generate_dummy_value(actual_return_type)
        body_snippet = f"""
	// TODO: REMOVE THIS DUMMY IMPLEMENTATION - Replace with actual logic
	const dummy: {actual_return_type} = {dummy_value};
	return responseSuccess(dummy);
"""

    # Write function body block
    out.write(
        TEMPL["METHOD_BODY_BLOCK"]
        % {"__block_name": body_block_name, "__snippet": body_snippet}
    )

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

        properties.append(
            f" * @property {{{opt}{type_str}{opt_end}}} {param.name} - {descr}{constraint_str}"
        )

    schema_description = ep.description if ep.description else f"{func_name} parameters"

    out.write(
        TEMPL["METHOD_SCHEMA_START"]
        % {
            "__schema_description": schema_description,
            "__schema_properties": "\n".join(properties),
            "__schema_name": schema_name,
        }
    )

    # Write schema fields
    for param in ep.parameters:
        zod_type = _get_zod_type(param, ep.mod if hasattr(ep, "mod") else None)
        out.write(
            TEMPL["METHOD_SCHEMA_FIELD"] % {"name": param.name, "zod_type": zod_type}
        )

    out.write(TEMPL["METHOD_SCHEMA_END"])


def _write_params_type(out, params_type: str, schema_name: str, func_name: str):
    """Write the TypeScript params type"""
    out.write(
        TEMPL["METHOD_PARAMS_TYPE"]
        % {
            "__function_description": func_name,
            "__params_type": params_type,
            "__schema_name": schema_name,
        }
    )


def _write_result_type(out, ep: Endpoint, result_type: str, func_name: str):
    """Write the TypeScript result type"""
    # Get the proper TypeScript return type from endpoint definition
    ts_type = _get_typescript_return_type(ep, ep.mod if hasattr(ep, "mod") else None)

    out.write(
        TEMPL["METHOD_RESULT_TYPE"]
        % {
            "__function_description": func_name,
            "__result_type": result_type,
            "__result_fields": ts_type,
        }
    )


def _collect_referenced_types(ep: Endpoint, mod: Module) -> set[str]:
    """
    Collect all custom types referenced by the endpoint's return type and parameters.
    Returns a set of type names that need to be imported.
    """
    referenced_types = set()

    # Check return type
    if ep.return_type:
        return_type_name = ep.return_type

        # Search for type by name (not ID)
        for type_obj in mod.flow.types.values():
            if type_obj.name == return_type_name:
                referenced_types.add(type_obj.name)
                break
        else:
            # Check enums if not found in types
            for enum_obj in mod.flow.enums.values():
                if enum_obj.name == return_type_name:
                    referenced_types.add(enum_obj.name)
                    break

    # Check parameters for custom types
    if ep.parameters:
        for param in ep.parameters:
            if param.type[0] == FieldType.CUSTOM and len(param.type) > 1:
                custom_type_id = param.type[1]

                # Check if it's a custom type or enum (by ID)
                if custom_type_id in mod.flow.types:
                    type_obj = mod.flow.types[custom_type_id]
                    referenced_types.add(type_obj.name)
                elif custom_type_id in mod.flow.enums:
                    enum_obj = mod.flow.enums[custom_type_id]
                    referenced_types.add(enum_obj.name)

    return referenced_types


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

            # Check if Result type should be created
            should_create_result = _should_create_result_type(ep, mod)

            # Build export statement
            exports = [func_name]

            # Add params type if there are parameters
            if ep.parameters:
                exports.append(f"type {params_type}")

            # Add result type only if it was created
            if should_create_result:
                exports.append(f"type {result_type}")

            export_str = ", ".join(exports)
            out.write(f"export {{ {export_str} }} from './{file_name}';\n")

    print(f"Generated {outfile}")


def _generate_methods_wrapper(self, mod: Module, output: str):
    """Generate the src/methods.ts wrapper file that re-exports from methods/index.ts"""
    mod_name = self.mod_name(mod)
    outfile = os.path.join(output, "src", "methods.ts")

    with open(outfile, "w") as out:
        out.write(
            TEMPL["METHODS_WRAPPER_FILE"]
            % {"__mod_name": mod_name, "__mod_name_camel": mod_name.capitalize()}
        )

    print(f"Generated {outfile}")
