#!/usr/bin/env python3

"""
JSON to Drizzle ORM Schema Converter

This module converts LiWE Flow JSON type definitions to Drizzle ORM SQLite table schemas.
"""


def _get_drizzle_type(field_type: str, size: int, is_array: bool) -> tuple[str, dict, bool]:
    """
    Maps JSON field type to Drizzle ORM column type.

    Args:
        field_type: The field type from JSON (str, num, boolean, date, json, etc.)
        size: The maximum size/length for the field
        is_array: Whether the field is an array type

    Returns:
        Tuple of (drizzle_type, options_dict, needs_type_annotation)
    """
    field_type = field_type.lower()
    options = {}
    needs_type_annotation = False

    # Arrays always need JSON serialization
    if is_array:
        drizzle_type = "text"
        options["mode"] = "json"
        needs_type_annotation = True
    elif field_type in ["str", "string", "text"]:
        drizzle_type = "text"
        if size and size > 0:
            options["length"] = size
    elif field_type in ["int", "num", "number"]:
        drizzle_type = "integer"
    elif field_type in ["float", "double", "real"]:
        drizzle_type = "real"
    elif field_type in ["bool", "boolean"]:
        # SQLite stores boolean as integer
        drizzle_type = "integer"
        options["mode"] = "boolean"
    elif field_type == "date":
        drizzle_type = "date"
    elif field_type == "datetime":
        # SQLite stores timestamp as integer
        drizzle_type = "integer"
        options["mode"] = "timestamp"
    elif field_type in ["json", "obj", "object"]:
        drizzle_type = "text"
        options["mode"] = "json"
        needs_type_annotation = True
    else:
        # Custom types default to text with JSON mode (need serialization)
        drizzle_type = "text"
        options["mode"] = "json"
        needs_type_annotation = True

    return drizzle_type, options, needs_type_annotation


def _format_drizzle_options(options: dict) -> str:
    """
    Formats Drizzle ORM options dictionary into TypeScript object literal.

    Args:
        options: Dictionary of options (e.g., {"length": 50, "mode": "json"})

    Returns:
        Formatted string like "{ length: 50 }" or empty string
    """
    if not options:
        return ""

    parts = []
    for key, value in options.items():
        if isinstance(value, str):
            parts.append(f"{key}: '{value}'")
        else:
            parts.append(f"{key}: {value}")

    return "{ " + ", ".join(parts) + " }"


def _pluralize_table_name(name: str) -> str:
    """
    Converts a table name to lowercase plural form.

    Args:
        name: Singular table name (e.g., "User")

    Returns:
        Lowercase plural form (e.g., "users")
    """
    name_lower = name.lower()

    # Simple pluralization rules
    if name_lower.endswith('s'):
        return name_lower
    elif name_lower.endswith('y'):
        return name_lower[:-1] + 'ies'
    elif name_lower.endswith(('ch', 'sh', 'x', 'z')):
        return name_lower + 'es'
    else:
        return name_lower + 's'


def _get_index_description(field_name: str, index_type: str) -> str:
    """
    Generates a description for an index based on field name and index type.

    Args:
        field_name: Name of the indexed field
        index_type: Type of index (u=unique, y/m=multi, *=array, f=fulltext)

    Returns:
        Human-readable description of the index purpose
    """
    descriptions = {
        'id': 'primary key lookup',
        'email': 'user lookup by email',
        'username': 'user lookup by username',
        'domain': 'efficient domain-based queries',
        'enabled': 'filtering active/inactive records',
        'deleted': 'filtering deleted records',
        'created': 'sorting by creation date',
        'updated': 'sorting by update date',
    }

    if field_name in descriptions:
        return descriptions[field_name]

    # Generate generic description
    if index_type == 'u':
        return f'unique constraint on {field_name}'
    elif index_type in ('y', 'm'):
        return f'efficient {field_name}-based queries'
    elif index_type == '*':
        return f'array index on {field_name}'
    elif index_type == 'f':
        return f'fulltext search on {field_name}'
    else:
        return f'index on {field_name} field'


def json_to_drizzle(type_def: dict) -> str:
    """
    Converts a JSON type definition to a Drizzle ORM SQLite table schema.

    Args:
        type_def: Dictionary containing the type definition with keys:
                  - name: Type name (e.g., "User")
                  - description: Type description
                  - db_table: Database table name (optional, defaults to pluralized lowercase name)
                  - fields: List of field definitions

    Returns:
        Formatted TypeScript string ready to be written to a file
    """
    name = type_def.get('name', 'Unknown')
    description = type_def.get('description', '')
    table_name = type_def.get('db_table', '')

    if not table_name:
        table_name = _pluralize_table_name(name)

    # Ensure table name is lowercase
    table_name = table_name.lower()

    # Variable name for the table (lowercase plural)
    var_name = table_name

    fields = type_def.get('fields', [])

    # Add automatic created/updated timestamp fields (hidden LiWE framework fields)
    auto_fields = [
        {
            'name': 'created',
            'type': 'datetime',
            'is_required': False,
            'is_array': False,
            'description': 'Record creation timestamp',
            'size': 0,
            'index': ''
        },
        {
            'name': 'updated',
            'type': 'datetime',
            'is_required': False,
            'is_array': False,
            'description': 'Record last update timestamp',
            'size': 0,
            'index': ''
        }
    ]
    fields = list(fields) + auto_fields

    # Build the output
    lines = []

    # Header comment
    lines.append("/**")
    if description:
        lines.append(f" * {description}")
    else:
        lines.append(f" * {name} table schema for Drizzle ORM")
    lines.append(" */")

    # Table definition start
    lines.append(f"export const {var_name} = sqliteTable( '{table_name}', {{")

    # Track fields with indexes for later
    indexed_fields = []

    # Process each field
    for i, field in enumerate(fields):
        field_name = field.get('name', '')
        field_type = field.get('type', 'str')
        is_required = field.get('is_required', False)
        is_array = field.get('is_array', False)
        field_desc = field.get('description', '')
        size = field.get('size', 0)
        index = field.get('index', '')

        # Convert size to int if it's a string
        if isinstance(size, str):
            try:
                size = int(size)
            except ValueError:
                size = 0

        # Add field comment
        comment_text = field_desc if field_desc else f"{field_name} field"
        # Use single-line comment for one-line descriptions
        if '\n' not in comment_text:
            lines.append(f"\t// {comment_text}")
        else:
            # Use multi-line comment for multi-line descriptions
            lines.append("\t/**")
            for comment_line in comment_text.split('\n'):
                lines.append(f"\t * {comment_line}")
            lines.append("\t */")

        # Get Drizzle type
        drizzle_type, options, needs_type_annotation = _get_drizzle_type(field_type, size, is_array)

        # Build field definition
        field_def_parts = [f"\t{field_name}: {drizzle_type}( '{field_name}'"]

        # Add options if present
        options_str = _format_drizzle_options(options)
        if options_str:
            field_def_parts.append(f", {options_str}")

        field_def_parts.append(" )")

        # Add modifiers
        modifiers = []

        # Primary key for id field with unique index
        if field_name == 'id' and index == 'u':
            modifiers.append(".primaryKey().$defaultFn( () => '' )")

        # Not null for required fields
        if is_required:
            modifiers.append(".notNull()")

        # Add TypeScript type annotation for complex types
        if needs_type_annotation:
            if is_array:
                # Map field type to TypeScript type for arrays
                if field_type in ["str", "string", "text"]:
                    modifiers.append(".$type<string[]>()")
                elif field_type in ["int", "num", "number"]:
                    modifiers.append(".$type<number[]>()")
                elif field_type in ["float", "double", "real"]:
                    modifiers.append(".$type<number[]>()")
                elif field_type in ["bool", "boolean"]:
                    modifiers.append(".$type<boolean[]>()")
                elif field_type == "date":
                    modifiers.append(".$type<Date[]>()")
                elif field_type == "datetime":
                    modifiers.append(".$type<Date[]>()")
                elif field_type in ["json", "obj", "object", "none", ""]:
                    modifiers.append(".$type<any[]>()")
                else:
                    # Custom type array
                    modifiers.append(f".$type<{field_type}[]>()")
            else:
                # Single complex type
                if field_type in ["json", "obj", "object", "none", ""]:
                    modifiers.append(".$type<any>()")
                else:
                    # Custom type
                    modifiers.append(f".$type<{field_type}>()")

        # Default timestamps
        if field_name in ('created', 'updated'):
            modifiers.append(".default( sql`CURRENT_TIMESTAMP` )")

        field_def = "".join(field_def_parts) + "".join(modifiers) + ","
        lines.append(field_def)

        # Track indexed fields
        if index and index.strip():
            indexed_fields.append({
                'name': field_name,
                'index_type': index
            })

        # Add blank line between fields (except for the last one)
        if i < len(fields) - 1:
            lines.append("")

    # Close fields definition and start indexes section
    lines.append("}, ( table: any ) => [")

    # Add indexes
    if indexed_fields:
        for i, idx_field in enumerate(indexed_fields):
            field_name = idx_field['name']
            index_type = idx_field['index_type']

            # Skip id field as it's already primary key
            if field_name == 'id' and index_type == 'u':
                continue

            # Generate index name
            index_name = f"idx_{table_name}_{field_name}"

            # Add index comment
            desc = _get_index_description(field_name, index_type)
            lines.append(f"\t// Index on {field_name} field for {desc}")

            # Add index definition
            if index_type == 'u':
                # Unique index
                lines.append(f"\tuniqueIndex( '{index_name}' ).on( table.{field_name} ),")
            else:
                # Regular index
                lines.append(f"\tindex( '{index_name}' ).on( table.{field_name} ),")

            # Add blank line between indexes (except for the last one)
            if i < len(indexed_fields) - 1:
                lines.append("")

    # Close indexes array and table definition
    lines.append("]")
    lines.append(");")
    lines.append("")

    # Add type inference with DB suffix
    lines.append("/**")
    lines.append(f" * Type inference for {name} table select operations")
    lines.append(" */")
    lines.append(f"export type {name}DB = typeof {var_name}.$inferSelect;")

    return "\n".join(lines)
