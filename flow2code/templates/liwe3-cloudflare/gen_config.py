#!/usr/bin/env python3

import os
from lib.types import Module
from texts import texts as TEMPL


# ==================================================================================================
# CONFIG FILES GENERATION
# ==================================================================================================

def generate_config_files(self, mod: Module, output: str):
	"""Generate package.json, tsconfig.json, and vitest.config.ts only if they don't exist"""
	mod_name = self.mod_name(mod)
	mod_name_camel = mod.name

	# Generate package.json only if it doesn't exist
	package_json_path = os.path.join(output, "package.json")
	if not os.path.exists(package_json_path):
		content = TEMPL["PACKAGE_JSON"] % {
			'__mod_name': mod_name,
			'__mod_name_camel': mod_name_camel
		}
		with self.create_file(package_json_path, mod) as f:
			f.write(content)
		print(f"Generated {package_json_path}")
	else:
		print(f"Skipped {package_json_path} (already exists)")

	# Generate tsconfig.json only if it doesn't exist
	tsconfig_path = os.path.join(output, "tsconfig.json")
	if not os.path.exists(tsconfig_path):
		with self.create_file(tsconfig_path, mod) as f:
			f.write(TEMPL["TSCONFIG_JSON"])
		print(f"Generated {tsconfig_path}")
	else:
		print(f"Skipped {tsconfig_path} (already exists)")

	# Generate vitest.config.ts only if it doesn't exist
	vitest_config_path = os.path.join(output, "vitest.config.ts")
	if not os.path.exists(vitest_config_path):
		with self.create_file(vitest_config_path, mod) as f:
			f.write(TEMPL["VITEST_CONFIG"])
		print(f"Generated {vitest_config_path}")
	else:
		print(f"Skipped {vitest_config_path} (already exists)")
