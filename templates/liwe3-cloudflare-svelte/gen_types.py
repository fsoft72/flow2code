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

	# Get snippet for custom types block
	custom_types_snippet = self.snippets.get("__types", "\n// Add custom types here\n")

	# Generate Zod schema for each type
	for type_obj in mod.types.values():
		# Convert Type object to dict format expected by json_to_zod
		# Note: json_to_zod will add "Schema" suffix, so we just use the original name
		type_dict = {
			'name': type_obj.name,
			'description': type_obj.description if hasattr(type_obj, 'description') else '',
			'fields': []
		}

		# Convert fields to dict format
		for field in type_obj.fields:
			# Skip fields without a name
			if not field.name or field.name.strip() == '':
				sys.stderr.write(f"WARNING: Skipping field without name in type '{type_obj.name}'\n")
				continue

			# Get size and min_length, ensuring they're integers
			size = field.size if hasattr(field, 'size') and field.size is not None else 0
			min_length = field.min_length if hasattr(field, 'min_length') and field.min_length is not None else 0

			field_dict = {
				'name': field.name,
				'type': field.type[1] if field.type[0].value == 'custom' else field.type[0].value,
				'is_required': field.required,
				'is_array': field.is_array,
				'description': field.description,
				'size': size,
				'min_length': min_length
			}
			type_dict['fields'].append(field_dict)

		# Generate Zod schema using json_to_zod
		zod_schema = json_to_zod(type_dict)

		# Replace the schema name to use Z prefix instead of Schema suffix
		# json_to_zod generates: "const {Name}Schema = z.object..."
		# We want: "const Z{Name} = z.object..."
		original_schema_name = f"{type_obj.name}Schema"
		new_schema_name = f"Z{type_obj.name}"
		zod_schema = zod_schema.replace(f"const {original_schema_name}", f"const {new_schema_name}")

		out.write(zod_schema)
		out.write("\n")

		# Always export both TypeScript type and Zod schema
		type_name = type_obj.name
		out.write(f"export type {type_name} = z.infer<typeof {new_schema_name}>;\n")
		out.write(f"export {{ {new_schema_name} }};\n\n")

	# Write custom types block for user code preservation
	out.write("/*=== f2c_start __types ===*/\n")
	out.write(custom_types_snippet)
	out.write("/*=== f2c_end __types ===*/\n")

	# Close the output file
	out.close()
	print(f"Generated {outfile}")
