#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from lib.const import FieldType
from texts import texts as TEMPL


# ==================================================================================================
# HELPER FUNCTIONS
# ==================================================================================================


def _create_action_name(ep: Endpoint, mod: Module) -> str:
    """Create action function name from endpoint, e.g., GET /system/admin/users -> system_admin_users"""
    # Remove leading /api if present
    path = ep.path.replace("/api/", "/").replace("/api", "")
    # Remove leading slash
    path = path.lstrip("/")
    # Replace slashes with underscores and remove path params
    parts = []
    for part in path.split("/"):
        if not part.startswith(":"):
            # Replace hyphens with underscores for valid function names
            parts.append(part.replace("-", "_").lower())

    return "_".join(parts)


def _get_typescript_return_type(ep: Endpoint, mod: Module = None) -> str:
    """
    Maps Endpoint return_type to TypeScript type string.
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
            # Search by name in types
            found = False
            for type_obj in mod.types.values():
                if type_obj.name == ep.return_type:
                    base = type_obj.name
                    found = True
                    break
            if not found:
                # Also check enums
                for enum_obj in mod.enums.values():
                    if enum_obj.name == ep.return_type:
                        base = enum_obj.name
                        found = True
                        break
            if not found:
                # Fallback to return_type as-is
                base = ep.return_type
        else:
            base = "any"

    # Handle arrays
    if ep.is_array:
        base += "[]"

    return base


def _get_params_type(ep: Endpoint, mod: Module) -> str:
    """Get the TypeScript type for parameters"""
    if not ep.parameters:
        return None

    # Build inline type object
    fields = []
    for param in ep.parameters:
        opt = "?" if not param.required else ""

        # Determine TypeScript type
        if param.type[0] == FieldType.STR:
            ts_type = "string"
        elif param.type[0] == FieldType.NUMBER or param.type[0] == FieldType.FLOAT:
            ts_type = "number"
        elif param.type[0] == FieldType.BOOL:
            ts_type = "boolean"
        elif param.type[0] == FieldType.DATE:
            ts_type = "string"
        elif param.type[0] == FieldType.DATETIME:
            ts_type = "Date"
        elif param.type[0] == FieldType.FILE:
            ts_type = "File"
        elif param.type[0] == FieldType.OBJECT:
            ts_type = "any"
        elif param.type[0] == FieldType.CUSTOM:
            # Look up the actual type name from the module by searching by name
            if len(param.type) > 1:
                custom_type_name = param.type[1]
                found = False
                # Search in types
                for type_obj in mod.types.values():
                    if type_obj.name == custom_type_name:
                        ts_type = type_obj.name
                        found = True
                        break
                if not found:
                    # Search in enums
                    for enum_obj in mod.enums.values():
                        if enum_obj.name == custom_type_name:
                            ts_type = enum_obj.name
                            found = True
                            break
                if not found:
                    # Use the name as-is
                    ts_type = custom_type_name
            else:
                ts_type = "any"
        else:
            ts_type = "any"

        # Handle arrays
        if param.is_array:
            ts_type += "[]"

        fields.append(f"\t{param.name}{opt}: {ts_type}")

    return "{\n" + ";\n".join(fields) + "\n}"


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================


def generate_file_actions(self, mod: Module, output: str):
    """Generate the actions.ts file with API client calls for each endpoint"""
    mod_name = self.mod_name(mod)

    # If no endpoints defined, don't generate actions file
    if not mod.endpoints or len(mod.endpoints) == 0:
        print(f"Skipping actions generation - no endpoints found")
        return

    # Create the src directory if it doesn't exist
    src_dir = os.path.join(output, "src")
    os.makedirs(src_dir, exist_ok=True)

    # Create the output file
    outfile = os.path.join(src_dir, "actions.ts")
    out = self.create_file(outfile, mod)

    # Collect custom types used in return types and parameters
    custom_types_needed = set()
    for ep in mod.endpoints.values():
        # Check return type
        if ep.return_type:
            return_type_lower = ep.return_type.lower()
            # Check if it's a custom type (not a built-in type)
            if return_type_lower not in [
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
            ]:
                # Search for the type by name in mod.types
                for type_obj in mod.types.values():
                    if type_obj.name == ep.return_type:
                        custom_types_needed.add(type_obj.name)
                        break
                # Also check enums
                for enum_obj in mod.enums.values():
                    if enum_obj.name == ep.return_type:
                        custom_types_needed.add(enum_obj.name)
                        break

        # Check parameters for custom types
        if ep.parameters:
            for param in ep.parameters:
                if param.type[0] == FieldType.CUSTOM and len(param.type) > 1:
                    custom_type_name = param.type[1]
                    # Search by name in types
                    for type_obj in mod.types.values():
                        if type_obj.name == custom_type_name:
                            custom_types_needed.add(type_obj.name)
                            break
                    # Also check enums
                    for enum_obj in mod.enums.values():
                        if enum_obj.name == custom_type_name:
                            custom_types_needed.add(enum_obj.name)
                            break

    # Write file header with imports
    out.write(TEMPL["ACTIONS_FILE_START"])

    # Add custom type imports if needed
    if custom_types_needed:
        type_imports = ", ".join(sorted(custom_types_needed))
        out.write(f"import type {{ {type_imports} }} from './types';\n")

    out.write("\n")

    # Get snippet for custom imports/code block at the beginning
    custom_actions_header_snippet = self.snippets.get(
        "actions", "\n// Add custom imports here\n"
    )

    # Write custom actions header block for user code preservation
    out.write("/*=== f2c_start actions ===*/\n")
    out.write(custom_actions_header_snippet)
    out.write("/*=== f2c_end actions ===*/\n\n")

    # Generate action for each endpoint
    for ep in mod.endpoints.values():
        _write_action(self, out, ep, mod)

    # Get snippet for custom actions block
    custom_actions_snippet = self.snippets.get(
        "__actions", "\n// Add custom actions here\n"
    )

    # Write custom actions block for user code preservation
    out.write("/*=== f2c_start __actions ===*/\n")
    out.write(custom_actions_snippet)
    out.write("/*=== f2c_end __actions ===*/\n")

    # Close the output file
    out.close()
    print(f"Generated {outfile}")


def _write_action(self, out, ep: Endpoint, mod: Module):
    """Write a single action function"""
    action_name = _create_action_name(ep, mod)
    method = ep.method.lower()
    path = ep.path if ep.path.startswith("/api") else f"/api{ep.path}"
    return_type = _get_typescript_return_type(ep, mod)

    # Determine if we need parameters
    has_params = len(ep.parameters) > 0
    params_type = _get_params_type(ep, mod) if has_params else None

    # Build function signature with LiWEResponse wrapper
    if has_params:
        func_sig = f"export const {action_name} = async ( params: {params_type} ): Promise<LiWEResponse<{return_type}>> => {{"
    else:
        func_sig = f"export const {action_name} = async (): Promise<LiWEResponse<{return_type}>> => {{"

    out.write(func_sig + "\n")

    # Build API call based on method
    if method == "get":
        if has_params:
            out.write(f"\tconst res = await apiClient.get( '{path}', params );\n")
        else:
            out.write(f"\tconst res = await apiClient.get( '{path}' );\n")
    elif method in ["post", "put", "patch"]:
        if has_params:
            out.write(f"\tconst res = await apiClient.{method}( '{path}', params );\n")
        else:
            out.write(f"\tconst res = await apiClient.{method}( '{path}' );\n")
    elif method == "delete":
        if has_params:
            out.write(f"\tconst res = await apiClient.delete( '{path}', params );\n")
        else:
            out.write(f"\tconst res = await apiClient.delete( '{path}' );\n")
    else:
        # Fallback to post
        if has_params:
            out.write(f"\tconst res = await apiClient.post( '{path}', params );\n")
        else:
            out.write(f"\tconst res = await apiClient.post( '{path}' );\n")

    # Get snippet for this action's custom code block
    action_snippet = self.snippets.get(action_name, "\n\t// Add custom code here\n")

    # Write custom code preservation block before return
    out.write("\n\t/*=== f2c_start " + action_name + " ===*/")
    out.write(action_snippet)
    out.write("\t/*=== f2c_end " + action_name + " ===*/\n")

    out.write("\n\treturn res;\n")
    out.write("};\n\n")
