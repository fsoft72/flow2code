#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import json_to_zod
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from lib.types import Module
from lib.json_to_zod import json_to_zod
from texts import texts as TEMPL


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================

def generate_file_types(self, mod: Module, output: str):
	"""Generate the TypeScript Zod schemas file for all types"""
	mod_name = self.mod_name(mod)

	# If no types defined, don't generate types file
	if not mod.types or len(mod.types) == 0:
		print(f"Skipping types generation - no types found")
		return

	# Create the src directory if it doesn't exist
	src_dir = os.path.join(output, "src")
	os.makedirs(src_dir, exist_ok=True)

	# Create the output file
	outfile = os.path.join(src_dir, "types.ts")
	out = self.create_file(outfile, mod)

	# Write file header with Zod import
	out.write("import { z } from 'zod';\n\n")

	# Generate Zod schema for each type
	for type_obj in mod.types.values():
		# Convert Type object to dict format expected by json_to_zod
		type_dict = {
			'name': f"Z{type_obj.name}",  # Prefix with Z
			'description': type_obj.description if hasattr(type_obj, 'description') else '',
			'fields': []
		}

		# Convert fields to dict format
		for field in type_obj.fields:
			field_dict = {
				'name': field.name,
				'type': field.type[1] if field.type[0].value == 'custom' else field.type[0].value,
				'is_required': field.required,
				'is_array': field.is_array,
				'description': field.description,
				'size': field.size if hasattr(field, 'size') else 0,
				'min_length': field.min_length if hasattr(field, 'min_length') else 0
			}
			type_dict['fields'].append(field_dict)

		# Generate Zod schema
		zod_schema = json_to_zod(type_dict)
		out.write(zod_schema)
		out.write("\n")

		# Generate TypeScript type from Zod schema
		schema_name = f"Z{type_obj.name}Schema"
		type_name = type_obj.name
		out.write(f"export type {type_name} = z.infer<typeof {schema_name}>;\n")
		out.write(f"export {{ {schema_name} }};\n\n")

	# Close the output file
	out.close()
	print(f"Generated {outfile}")
