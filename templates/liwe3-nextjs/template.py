#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.types import Module, Endpoint

from texts import texts as TEMPL

from gen_types import generate_file_types, _gen_type
from gen_urls import generate_file_urls, _gen_url
from gen_actions import generate_file_actions, _gen_action_enum, _gen_store_fn, _gen_action
from gen_reducers import generate_file_reducer
from gen_initial_state import generate_file_initial_state
from gen_reducer_functions import generate_file_reducer_functions, _gen_reducer_function

class Template( TemplateBase ):
	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nextjs"

	def code ( self, mod:Module, flow: any, output: str ):
		super().code( mod, flow, output )
		self.generate_file_types ( mod, output )
		self.generate_file_urls ( mod, output )
		self.generate_file_actions ( mod, output )
		self.generate_file_reducer ( mod, output )
		self.generate_file_initial_state ( mod, output )
		self.generate_file_reducer_functions ( mod, output )

	@staticmethod
	def endpoint_action_name(ep: Endpoint, prefix=''):
		name = prefix + ep.path.replace("/", "_").lower().split(":")[0]
		name = name.replace("-", "_").replace("__", "_")
		if name.startswith("_"): name = name[1:]
		if name.endswith("_"): name = name[:-1]

		return name

Template.generate_file_types = generate_file_types
Template._gen_type = _gen_type

Template.generate_file_urls = generate_file_urls
Template._gen_url = _gen_url

Template.generate_file_actions = generate_file_actions
Template._gen_action_enum = _gen_action_enum
Template._gen_store_fn = _gen_store_fn
Template._gen_action = _gen_action

Template.generate_file_reducer = generate_file_reducer

Template.generate_file_initial_state = generate_file_initial_state

Template.generate_file_reducer_functions = generate_file_reducer_functions
Template._gen_reducer_function = _gen_reducer_function