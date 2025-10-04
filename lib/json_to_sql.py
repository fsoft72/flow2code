#!/usr/bin/env python3

"""
JSON to SQL Schema Converter

This module converts LiWE Flow JSON type definitions to SQL table schemas.
Supports multiple SQL dialects: SQLite, MySQL, and MariaDB.
"""


def _get_sql_type(field_type: str, size: int, is_array: bool, dialect: str) -> str:
	"""
	Maps JSON field type to SQL column type based on dialect.

	Args:
		field_type: The field type from JSON (str, num, boolean, date, json, etc.)
		size: The maximum size/length for the field
		is_array: Whether the field is an array type
		dialect: SQL dialect (sqlite, mysql, mariadb)

	Returns:
		SQL type string
	"""
	field_type = field_type.lower()
	dialect = dialect.lower()

	# Handle array types - stored as JSON/TEXT
	if is_array:
		if dialect == 'sqlite':
			return 'TEXT'
		else:  # mysql/mariadb
			return 'JSON'

	# Map field types to SQL types
	if field_type in ["str", "string", "text"]:
		if dialect == 'sqlite':
			return f'VARCHAR({size})' if size and size > 0 else 'VARCHAR(200)'
		else:  # mysql/mariadb
			return f'VARCHAR({size})' if size and size > 0 else 'VARCHAR(200)'

	elif field_type in ["int", "num", "number"]:
		return 'INTEGER'

	elif field_type in ["float", "double", "real"]:
		if dialect == 'sqlite':
			return 'REAL'
		else:  # mysql/mariadb
			return 'DOUBLE'

	elif field_type in ["bool", "boolean"]:
		if dialect == 'sqlite':
			return 'INTEGER'  # SQLite uses 0/1 for boolean
		else:  # mysql/mariadb
			return 'BOOLEAN'

	elif field_type == "date":
		return 'DATE'

	elif field_type == "datetime":
		if dialect == 'sqlite':
			return 'DATETIME'
		else:  # mysql/mariadb
			return 'DATETIME'

	elif field_type in ["json", "obj", "object"]:
		if dialect == 'sqlite':
			return 'TEXT'
		else:  # mysql/mariadb
			return 'JSON'

	else:
		# Custom types default to VARCHAR
		if dialect == 'sqlite':
			return 'VARCHAR(200)'
		else:
			return 'VARCHAR(200)'


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


def json_to_sql(type_def: dict, dialect: str = 'sqlite') -> str:
	"""
	Converts a JSON type definition to SQL table schema.

	Args:
		type_def: Dictionary containing the type definition with keys:
				  - name: Type name (e.g., "User")
				  - description: Type description
				  - db_table: Database table name (optional, defaults to pluralized lowercase name)
				  - fields: List of field definitions
		dialect: SQL dialect to use (sqlite, mysql, mariadb). Defaults to sqlite.

	Returns:
		Formatted SQL string ready to be written to a file

	Raises:
		ValueError: If dialect is not supported
	"""
	# Validate dialect
	dialect = dialect.lower()
	if dialect not in ['sqlite', 'mysql', 'mariadb']:
		raise ValueError(f"Unsupported SQL dialect: {dialect}. Supported dialects: sqlite, mysql, mariadb")

	name = type_def.get('name', 'Unknown')
	description = type_def.get('description', '')
	table_name = type_def.get('db_table', '')

	if not table_name:
		table_name = _pluralize_table_name(name)

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

	# Header comment with description
	if description:
		lines.append(f"-- {description}")
	else:
		lines.append(f"-- {name} table schema")

	# Table creation statement
	lines.append(f"CREATE TABLE {name} (")

	# Track fields with indexes for later
	indexed_fields = []
	primary_key_field = None

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

		# Add field comment above the field definition
		if field_desc:
			lines.append(f"    -- {field_name}: {field_desc}")

		# Get SQL type
		sql_type = _get_sql_type(field_type, size, is_array, dialect)

		# Build field definition
		field_def = f"    {field_name} {sql_type}"

		# Add PRIMARY KEY for id field with unique index
		if field_name == 'id' and index == 'u':
			field_def += " PRIMARY KEY"
			primary_key_field = field_name

		# Add NOT NULL for required fields (except id which already has PRIMARY KEY)
		elif is_required:
			field_def += " NOT NULL"

		# Add default for timestamp fields
		if field_name in ('created', 'updated'):
			if dialect == 'sqlite':
				field_def += " DEFAULT CURRENT_TIMESTAMP"
			else:  # mysql/mariadb
				field_def += " DEFAULT CURRENT_TIMESTAMP"
				if field_name == 'updated':
					field_def += " ON UPDATE CURRENT_TIMESTAMP"

		# Add comma for all fields except the last one
		if i < len(fields) - 1:
			field_def += ","

		lines.append(field_def)

		# Track indexed fields (skip id field as it's already primary key)
		if index and index.strip() and not (field_name == 'id' and index == 'u'):
			indexed_fields.append({
				'name': field_name,
				'index_type': index,
				'description': field_desc
			})

	# Close table definition
	lines.append(");")
	lines.append("")

	# Add indexes
	if indexed_fields:
		for idx_field in indexed_fields:
			field_name = idx_field['name']
			index_type = idx_field['index_type']
			field_desc = idx_field['description']

			# Generate index name
			index_name = f"idx_{table_name}_{field_name}"

			# Add index comment
			if field_desc:
				lines.append(f"-- Index on {field_name}: {field_desc}")
			else:
				lines.append(f"-- Index on {field_name}")

			# Add index definition
			if index_type == 'u':
				# Unique index
				lines.append(f"CREATE UNIQUE INDEX {index_name} ON {name}({field_name});")
			else:
				# Regular index
				lines.append(f"CREATE INDEX {index_name} ON {name}({field_name});")

			lines.append("")

	return "\n".join(lines).rstrip() + "\n"
