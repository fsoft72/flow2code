#!/usr/bin/env python3

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from lib.types import Module


# ==================================================================================================
# MAIN GENERATION FUNCTION
# ==================================================================================================

def generate_file_events(self, mod: Module, output: str):
	"""Generate the TypeScript events constants file"""
	mod_name = self.mod_name(mod).upper()

	# If no events defined, don't generate events file
	if not mod.events or len(mod.events) == 0:
		print(f"Skipping events generation - no events found")
		return

	# Create the src directory if it doesn't exist
	src_dir = os.path.join(output, "src")
	os.makedirs(src_dir, exist_ok=True)

	# Create the output file
	outfile = os.path.join(src_dir, "events.ts")
	out = self.create_file(outfile, mod)

	# Generate constant for each event
	for event_obj in mod.events.values():
		# Extract event name parts (e.g., "user.create" -> ["user", "create"])
		event_name_parts = event_obj.name.split('.')

		# Build constant name: MODULE_EVENT_EVENTNAME
		if len(event_name_parts) > 1:
			# If event name has parts like "user.create", use the last part
			const_name = f"{mod_name}_EVENT_{event_name_parts[-1].upper()}"
		else:
			# Otherwise use the whole name
			const_name = f"{mod_name}_EVENT_{event_obj.name.upper()}"

		# Replace any invalid characters with underscores
		const_name = const_name.replace('-', '_').replace('.', '_')

		# Write comment if description exists
		if event_obj.description and event_obj.description.strip():
			out.write(f"// {event_obj.description.strip()}\n")

		# Write the constant
		out.write(f"export const {const_name} = '{event_obj.name}';\n")
		out.write("\n")

	# Close the output file
	out.close()
	print(f"Generated {outfile}")
