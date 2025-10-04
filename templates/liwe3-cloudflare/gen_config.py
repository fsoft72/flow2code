#!/usr/bin/env python3

import os
from lib.types import Module
from texts import texts as TEMPL


# ==================================================================================================
# CONFIG FILES GENERATION
# ==================================================================================================

def generate_config_files(self, mod: Module, output: str):
	"""Generate package.json, tsconfig.json, and vitest.config.ts"""
	mod_name = self.mod_name(mod)
	mod_name_camel = mod.name

	# Generate package.json
	package_json_path = os.path.join(output, "package.json")
	with open(package_json_path, 'w') as f:
		content = TEMPL["PACKAGE_JSON"] % {
			'__mod_name': mod_name,
			'__mod_name_camel': mod_name_camel
		}
		f.write(content)
	print(f"Generated {package_json_path}")

	# Generate tsconfig.json
	tsconfig_path = os.path.join(output, "tsconfig.json")
	with open(tsconfig_path, 'w') as f:
		f.write(TEMPL["TSCONFIG_JSON"])
	print(f"Generated {tsconfig_path}")

	# Generate vitest.config.ts
	vitest_config_path = os.path.join(output, "vitest.config.ts")
	with open(vitest_config_path, 'w') as f:
		f.write(TEMPL["VITEST_CONFIG"])
	print(f"Generated {vitest_config_path}")
