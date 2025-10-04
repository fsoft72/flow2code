#!/usr/bin/env python3

"""
JSON to Zod Schema Converter

This module converts LiWE Flow JSON type definitions to Zod validation schemas.
"""


def _get_zod_type(field_type: str, is_array: bool, is_required: bool) -> str:
    """
    Maps JSON field type to Zod schema type.

    Args:
        field_type: The field type from JSON (str, num, boolean, date, json, etc.)
        is_array: Whether the field is an array type
        is_required: Whether the field is required

    Returns:
        Base Zod type string (e.g., "z.string()", "z.coerce.number()")
    """
    field_type = field_type.lower()

    # Map field types to Zod types
    if field_type in ["str", "string", "text"]:
        return "z.string()"
    elif field_type in ["int", "num", "number", "float", "double", "real"]:
        # Use coerce for numbers to handle string inputs
        return "z.coerce.number()"
    elif field_type in ["bool", "boolean"]:
        # Use coerce for booleans to handle string inputs
        return "z.coerce.boolean()"
    elif field_type == "date":
        # Date strings
        return "z.string()"
    elif field_type == "datetime":
        # DateTime strings or Date objects
        return "z.coerce.date()"
    elif field_type in ["json", "obj", "object"]:
        # Generic JSON/object type
        return "z.any()"
    elif field_type == "file":
        # File uploads
        return "z.any()"
    else:
        # Custom types or unknown types default to any
        return "z.any()"


def _add_validation_constraints(zod_chain: str, field: dict) -> str:
    """
    Adds validation constraints to a Zod schema chain.

    Args:
        zod_chain: The current Zod schema chain
        field: Field definition dictionary

    Returns:
        Updated Zod schema chain with constraints
    """
    field_type = field.get('type', 'str').lower()
    size = field.get('size', 0)
    min_length = field.get('min_length', 0)

    # Convert size to int if it's a string
    if isinstance(size, str):
        try:
            size = int(size)
        except ValueError:
            size = 0

    # Convert min_length to int if it's a string
    if isinstance(min_length, str):
        try:
            min_length = int(min_length)
        except ValueError:
            min_length = 0

    # String validations
    if field_type in ["str", "string", "text"]:
        # Min length validation
        if min_length > 0:
            field_name = field.get('name', 'field')
            zod_chain += f".min( {min_length}, '{field_name.capitalize()} is required' )"

        # Max length validation
        if size > 0:
            field_name = field.get('name', 'field')
            zod_chain += f".max( {size}, '{field_name.capitalize()} must be at most {size} characters' )"

    # Number validations
    elif field_type in ["int", "num", "number", "float", "double", "real"]:
        # Add min/max if specified (using size as max for numbers)
        if min_length > 0:
            zod_chain += f".min( {min_length} )"
        if size > 0:
            zod_chain += f".max( {size} )"

    return zod_chain


def _format_field_comment(field: dict) -> list[str]:
    """
    Formats JSDoc-style comment for a field.

    Args:
        field: Field definition dictionary

    Returns:
        List of comment lines
    """
    field_name = field.get('name', '')
    field_type = field.get('type', 'str')
    is_array = field.get('is_array', False)
    is_required = field.get('is_required', False)
    description = field.get('description', '')
    size = field.get('size', 0)
    min_length = field.get('min_length', 0)

    # Convert size to int if it's a string
    if isinstance(size, str):
        try:
            size = int(size)
        except ValueError:
            size = 0

    # Build type annotation
    type_annotation = field_type
    if is_array:
        type_annotation += "[]"
    if not is_required:
        type_annotation = f"[{type_annotation}]"  # Optional

    # Build comment parts
    parts = []

    # Main description
    if description:
        parts.append(description)
    else:
        parts.append(f"{field_name} field")

    # Add constraints info
    constraints = []
    if is_required:
        constraints.append("required")
    if size > 0:
        if field_type in ["str", "string", "text"]:
            constraints.append(f"max {size} chars")
        else:
            constraints.append(f"max {size}")
    if min_length > 0:
        if field_type in ["str", "string", "text"]:
            constraints.append(f"min {min_length} chars")
        else:
            constraints.append(f"min {min_length}")

    if constraints:
        parts.append(f"({', '.join(constraints)})")

    return [
        f" * @property {{{type_annotation}}} {field_name} - {' '.join(parts)}"
    ]


def json_to_zod(type_def: dict) -> str:
    """
    Converts a JSON type definition to a Zod validation schema.

    Args:
        type_def: Dictionary containing the type definition with keys:
                  - name: Type name (e.g., "User")
                  - description: Type description
                  - fields: List of field definitions

    Returns:
        Formatted TypeScript/Zod string ready to be written to a file
    """
    name = type_def.get('name', 'Unknown')
    description = type_def.get('description', '')
    fields = type_def.get('fields', [])

    # Build the output
    lines = []

    # Schema JSDoc header
    lines.append("/**")
    if description:
        lines.append(f" * {description}")
    else:
        lines.append(f" * Schema for {name}")
    lines.append(" *")

    # Add field documentation
    for field in fields:
        field_lines = _format_field_comment(field)
        lines.extend(field_lines)

    lines.append(" */")

    # Schema definition start
    schema_name = f"{name}Schema"
    lines.append(f"const {schema_name} = z.object( {{")

    # Process each field
    for i, field in enumerate(fields):
        field_name = field.get('name', '')
        field_type = field.get('type', 'str')
        is_array = field.get('is_array', False)
        is_required = field.get('is_required', False)

        # Get base Zod type
        zod_type = _get_zod_type(field_type, is_array, is_required)

        # Add validation constraints
        zod_chain = _add_validation_constraints(zod_type, field)

        # Handle arrays
        if is_array:
            zod_chain += ".array()"

        # Handle optional fields
        if not is_required:
            zod_chain += ".optional()"

        # Add default for specific fields
        if field_name == "weight" and field_type in ["int", "num", "number", "float", "double", "real"]:
            zod_chain += ".default( 1.0 )"

        # Format the field line
        field_line = f"\t{field_name}: {zod_chain},"
        lines.append(field_line)

    # Close schema definition
    lines.append("} );")
    lines.append("")

    return "\n".join(lines)
