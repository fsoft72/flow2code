#!/usr/bin/env python3

# import TemplateBase
from lib.template_base import TemplateBase
from lib.types import Module

from gen_config import generate_config_files
from gen_types import generate_file_types
from gen_actions import generate_file_actions
from gen_index import generate_file_index


class Template(TemplateBase):
	def __init__(self):
		super().__init__()
		self.name = "liwe3-cloudflare-svelte"

	def code(self, mod: Module, flow: any, output: str):
		super().code(mod, flow, output)

		# Append module name to output path
		import os
		mod_name = self.mod_name(mod)
		output = os.path.join(output, mod_name)

		self.generate_config_files(mod, output)
		self.generate_file_types(mod, output)
		self.generate_file_actions(mod, output)
		self.generate_file_index(mod, output)


# Config files generation
Template.generate_config_files = generate_config_files

# Types file generation
Template.generate_file_types = generate_file_types

# Actions file generation
Template.generate_file_actions = generate_file_actions

# Index file generation
Template.generate_file_index = generate_file_index
