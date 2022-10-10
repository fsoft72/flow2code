#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template import TemplateBase

from texts import texts as TEMPL

class Template( TemplateBase ):

	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nodejs"

	def _generate_endpoint ( self, mod, output ):
		mod_name = self.mod_name( mod )

		# create the output directory
		outdir = os.path.join( output, "server", "modules", mod_name )
		os.makedirs( outdir, exist_ok=True,  )

		# create the output file
		outfile = os.path.join( outdir, 'endpoints.ts' )

		# extract snippets
		self.extract_snippets( mod, outfile )

		self._prepare_methods( mod )

		out = open( outfile, 'w' )

		# write the header
		out.write ( TEMPL [ 'HEADER_START' ] % self.snippets )

		# close the output file
		out.close()
		print( "Generated", outfile )

	def _prepare_methods ( self, mod ):
		# prepare the methods
		methods = []
		for ep in mod['endpoints'].values():
			name = self.endpoint_mk_function ( ep )
			methods.append( name )

		# convert methods to a string, adding a new line every 5 elements
		methods_str = ''
		for i, m in enumerate( methods ):
			methods_str += m
			if i % 5 == 0:
				methods_str += ',\n\t'
			else:
				methods_str += ', '

		self.snippets[ '_methods' ] = methods_str

	def code ( self, mod, output ):
		self._generate_endpoint ( mod, output )
