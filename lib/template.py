#!/usr/bin/env python3

import re

# RegExp that extracts the name from d2r_start block_name and d2r_end block_name
re_block_name = re.compile( r'.*d2r_(start|end)\s+(?P<name>[a-zA-Z0-9_]+)\s*')

class TemplateBase:
	snippets = {}

	def __init__( self ):
		self.name = "Base Template"

	def __str__( self ):
		return self.name

	def extract_snippets ( self, mod, fname ):
		# load the whole fname in memory
		# and extracts all code contained in /* dr_start (block_name) */ and /* dr_end (block_name) */
		# using the block_name as key in the snippets dictionary
		# the code is stored in the snippets dictionary as a list of lines

		# open the file
		lines = open( fname, 'r' ).readlines()

		# initialize the snippets dictionary
		self.snippets = {}

		# initialize the current block name
		block_name = None

		# initialize the current block lines
		block_lines = []

		# iterate over the lines
		for line in lines:
			# check if the line starts with dr_start
			if line.find( "d2r_start" ) != -1:
				g = re_block_name.match( line )
				block_name = g.group( 'name' )
				# initialize the block lines
				block_lines = []

			# check if the line starts with dr_end
			elif line.find( "d2r_end" ) != -1:
				g = re_block_name.match( line )
				block_name = g.group( 'name' )

				# store the block lines in the snippets dictionary
				self.snippets [ block_name ] = ''.join ( block_lines )

				# initialize the block lines
				block_lines = []

			# check if the block name is not None
			elif block_name is not None:
				# append the line to the block lines
				block_lines.append( line )

		self.snippets.update( {
			'__name_camel': mod [ 'name' ].strip (),
			'__name_lower': mod [ 'name' ].lower().strip().replace( ' ', '_' ),
			'__name_upper': mod [ 'name' ].upper().strip().replace( ' ', '_' ),
		} )

	def code ( self, mod, output ):
		print( "=== code() method not refined for", self.name )

	def mod_name ( self, mod ):
		return mod [ 'name' ].lower().strip().replace( ' ', '_' )

	def endpoint_mk_function ( self, ep ):
		name = f"""{ep['method']}_{ep['url']}""".lower().replace ( "/", "_" )

		# remove all characters that are not a-z, 0-9 or _
		name = re.sub( r'[^a-z0-9_-]', '', name )

		# remove all double underscores
		name = re.sub( r'__+', '_', name )
		name = name.strip( '_' )
		return name