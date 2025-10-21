#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import json_to_drizzle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from lib.types import Module
from lib.json_to_drizzle import json_to_drizzle
from texts import texts as TEMPL


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================

def generate_file_schema(self, mod: Module, output: str):
	"""Generate the schema.ts file with Drizzle ORM table definitions"""
	mod_name = self.mod_name(mod)

	# Filter types that have a coll_table (db_table) defined
	types_with_db = []
	for type_obj in mod.types.values():
		# Check if type has coll_table attribute and it's not empty
		if hasattr(type_obj, 'coll_table') and type_obj.coll_table:
			types_with_db.append(type_obj)

	# If no types have coll_table, don't generate schema.ts
	if not types_with_db:
		print(f"Skipping schema.ts generation - no types with coll_table found")
		return

	# Collect all custom types used in fields that need JSON serialization
	# Only include types that:
	# 1. Are actually defined in the module's types
	# 2. Don't have a db_table (those are defined in schema.ts itself)
	custom_types_needed = set()
	for type_obj in types_with_db:
		for field in type_obj.fields:
			# Check if field uses a custom type
			if field.type[0].value == 'custom':
				custom_type_name = field.type[1]
				# Check if this type exists in the module
				if custom_type_name in mod.types:
					referenced_type = mod.types[custom_type_name]
					# Only import if it doesn't have a db_table (not in schema.ts)
					if not (hasattr(referenced_type, 'coll_table') and referenced_type.coll_table):
						custom_types_needed.add(custom_type_name)

	# Create the output file
	outfile = os.path.join(output, "src", "schema.ts")
	out = self.create_file(outfile, mod)

	# Write file header with imports
	out.write(TEMPL["SCHEMA_FILE_START"])

	# Add custom type imports if needed
	if custom_types_needed:
		type_imports = ", ".join(sorted(custom_types_needed))
		out.write(f"import type {{ {type_imports} }} from './types';\n\n")

	# Generate table definitions for each type
	for type_obj in types_with_db:
		# Convert Type object to dict format expected by json_to_drizzle
		type_dict = {
			'name': type_obj.name,
			'description': '',  # Type class doesn't have description attribute
			'db_table': type_obj.coll_table,  # Use coll_table instead of db_table
			'fields': []
		}

		# Convert fields to dict format
		for field in type_obj.fields:
			# Convert index flags back to string format
			index_str = ''
			if hasattr(field, 'idx_unique') and field.idx_unique:
				index_str = 'u'
			elif hasattr(field, 'idx_multi') and field.idx_multi:
				index_str = 'y'
			elif hasattr(field, 'idx_array') and field.idx_array:
				index_str = '*'
			elif hasattr(field, 'idx_fulltext') and field.idx_fulltext:
				index_str = 'f'

			field_dict = {
				'name': field.name,
				'type': field.type[1] if field.type[0].value == 'custom' else field.type[0].value,
				'is_required': field.required,
				'is_array': field.is_array,
				'description': field.description,
				'size': field.size if hasattr(field, 'size') else 0,
				'index': index_str
			}
			type_dict['fields'].append(field_dict)

		# Generate Drizzle schema using the library
		drizzle_code = json_to_drizzle(type_dict)
		out.write(drizzle_code)
		out.write("\n\n")

	# Write file footer
	out.write(TEMPL["SCHEMA_FILE_END"])

	# Close the output file
	out.close()
	print(f"Generated {outfile}")
