#!/usr/bin/env python3

"""
This script converts a flow file to code

Author: Fabio Rotondo <fabio.rotondo@gmail.com>

See: https://flow.liwe.org
"""

import argparse
import json
import os
import sys
import importlib

VERSION='0.1.0'

class Flow2Code:
	# List of modules to be converted
	modules = []

	# The template module instance
	template = None

	def __init__( self, flow, template ):
		self._open_flow ( flow )
		self._open_template ( template )

	def _open_flow ( self, flow_fname ):
		data = json.loads( open( flow_fname, 'r' ).read() )

		m = ''
		if 'modules' in data:
			m = 'modules'
		elif 'mods' in data:
			m = 'mods'

		if m:
			for mod in data[ m ].values():
				self.modules.append( mod )
		else:
			self.modules.append( data )

	def _open_template ( self, template_fname ):
		# instance the template file from template_fname
		# and assign it to self.template

		# import the template module
		mod_path = os.path.join( os.path.join( "templates", template_fname ) ) #, 'template.py' )
		sys.path.append( mod_path )
		template_module = importlib.import_module( 'template' )

		# create the template instance
		self.template = template_module.Template()
		sys.path.pop()

	def code ( self, outdir ):
		for m in self.modules:
			self.template.code( m, outdir )


if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Convert a flow file to Code using a template' )
	parser.add_argument( 'flow', help='Flow file to convert' )
	parser.add_argument( '-o', '--output', help='Output directory' )
	parser.add_argument( '-t', '--template', help='Template file' )
	parser.add_argument( '-v', '--version', action='version', version='%(prog)s ' + VERSION )

	args = parser.parse_args()

	f2c = Flow2Code( args.flow, args.template )
	res = f2c.code ( args.output )