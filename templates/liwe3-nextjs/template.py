#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.types import Module

from texts import texts as TEMPL

from gen_types import generate_file_types

class Template( TemplateBase ):
	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nextjs"

	def code ( self, mod, output ):
		self.generate_file_types ( mod, output )

Template.generate_file_types = generate_file_types