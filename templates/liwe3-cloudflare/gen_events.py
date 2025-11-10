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
		# Convert event name to constant name
		# If event contains 'call': "system.call.user.create" -> "SYSTEM_CALL_USER_CREATE"
		# Otherwise add 'EVENT': "system.user_create" -> "SYSTEM_EVENT_USER_CREATE"

		if 'call' in event_obj.name.lower():
			# Event contains 'call', just convert to uppercase and replace dots/hyphens
			const_name = event_obj.name.upper().replace('.', '_').replace('-', '_')
		else:
			# Event doesn't contain 'call', add 'EVENT' after first part
			parts = event_obj.name.split('.')
			if len(parts) > 1:
				# e.g., "system.user_create" -> ["system", "user_create"] -> "SYSTEM_EVENT_USER_CREATE"
				const_name = f"{parts[0].upper()}_EVENT_{'_'.join(parts[1:]).upper().replace('-', '_')}"
			else:
				# Single part name, add EVENT prefix
				const_name = f"EVENT_{event_obj.name.upper().replace('-', '_')}"

		# Write comment if description exists
		if event_obj.description and event_obj.description.strip():
			out.write(f"// {event_obj.description.strip()}\n")

		# Write the constant
		out.write(f"export const {const_name} = '{event_obj.name}';\n")
		out.write("\n")

	# Close the output file
	out.close()
	print(f"Generated {outfile}")
