#!/usr/bin/env python3

# import TemplateBase
from lib.template_base import TemplateBase
from lib.types import Module

from gen_index import generate_file_index
from gen_perms import generate_file_perms
from gen_methods import generate_file_methods
from gen_schema import generate_file_schema
from gen_sql import generate_file_sql
from gen_config import generate_config_files


class Template(TemplateBase):
	def __init__(self):
		super().__init__()
		self.name = "liwe3-cloudflare"

	def code(self, mod: Module, flow: any, output: str):
		super().code(mod, flow, output)

		# Append module name to output path
		import os
		mod_name = self.mod_name(mod)
		output = os.path.join(output, mod_name)

		self.generate_config_files(mod, output)
		self.generate_file_schema(mod, output)
		self.generate_file_sql(mod, output)
		self.generate_file_perms(mod, output)
		self.generate_file_methods(mod, output)
		self.generate_file_index(mod, output)


# Index.ts file methods
Template.generate_file_index = generate_file_index

# Perms.ts file methods
Template.generate_file_perms = generate_file_perms

# Methods file generation
Template.generate_file_methods = generate_file_methods

# Schema.ts file generation
Template.generate_file_schema = generate_file_schema

# SQL file generation
Template.generate_file_sql = generate_file_sql

# Config files generation
Template.generate_config_files = generate_config_files
