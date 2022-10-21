#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.types import Module

from texts import texts as TEMPL

from gen_endpoints import generate_file_endpoints, _endpoint_definition, _prepare_methods_names, _typed_dict
from gen_methods   import generate_file_methods, _generate_endpoint, _generate_function
from gen_types     import generate_file_types, _gen_type

class Template( TemplateBase ):
	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nodejs"

	def types_and_enums_list ( self, mod: Module, *, add_obj = False ):
		k = list ( [ x.name for x in mod.types.values () ] ) + list ( [ x.name + "Keys" for x in mod.types.values () ] ) +  list ( [ x.name for x in mod.enums.values () ] )

		if add_obj:
			k += list ( [ x.name + "Obj" for x in mod.enums.values () ] )

		k.sort ()

		return k

	def code ( self, mod: Module, flow: any, output: str ):
		super().code( mod, flow, output )
		self.generate_file_endpoints ( mod, output )
		self.generate_file_methods ( mod, output )
		self.generate_file_types ( mod, output )

# Endpoints.ts file methods
Template.generate_file_endpoints = generate_file_endpoints
Template._endpoint_definition = _endpoint_definition
Template._prepare_methods_names = _prepare_methods_names
Template._typed_dict = _typed_dict

# Methods.ts file
Template.generate_file_methods = generate_file_methods
Template._generate_endpoint = _generate_endpoint
Template._generate_function = _generate_function

# Types.ts file
Template.generate_file_types = generate_file_types
Template._gen_type = _gen_type