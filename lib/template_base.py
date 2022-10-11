#!/usr/bin/env python3

import re
import os
from collections import defaultdict

from .const import FieldType

# RegExp that extracts the name from d2r_start block_name and d2r_end block_name
re_block_name = re.compile( r'.*(d2r|f2c)_(start|end)\s+(?P<name>[a-zA-Z0-9_]+)\s*')

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

		self.snippets = {}

		if not os.path.isfile( fname ): return

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

		# convert snippets to a defaultdict
		self.snippets = defaultdict( lambda: '', self.snippets )

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

	def prepare_field ( self, field, template, template_obj, honour_float = False, file_is_null = False, use_enums = False ):
		print ( "=== F: ", field )

		dct = {
			"name": field.get ( "name", "" ),
			"type": "any",
			"type_obj": False,
			"required": field.get ( "required", False ),
			"private": field.get ( "private", False ),
			"description": field.get ( "description", "" ),
			"opt": '',
			"param_default": field.get ( "default" ),
			"is_array": field.get ( "is_array", False ),
			"default": field.get ( "default", None ),
		}

		# The template param holds the default template string to be used
		# it could change if we need to use the _OBJ version of the template
		templ = template

		if dct [ 'param_default' ] == None:
			dct [ 'param_default' ] = 'undefined'

		if dct [ 'required' ]:
			dct [ '_req' ] = 'true'
			dct [ '_is_req' ] = 'req'
			dct [ 'param_default' ] = ''
		else:
			dct [ 'opt' ] = '?'
			dct [ '_is_req' ] = 'opt'
			dct [ '_req' ] = 'false'

		if dct [ 'private' ]:
			dct [ 'private' ] = 'true'
		else:
			dct [ 'private' ] = 'false'

		"""
		if ( field.req == 'opt' ) and ( dct [ 'param_default' ] == 'undefined' ):
			dct [ 'param_default' ] = ''
		"""

		_typ = field.get ( "type", "" )

		print ( "=== _typ: ", _typ )

		if _typ == FieldType.STR.value:
			dct [ 'type' ] = 'string'
			if dct [ 'param_default' ] and dct [ 'param_default' ] != 'undefined':
				dct [ 'param_default' ] = '"%s"' % dct [ 'param_default' ]
		elif _typ == FieldType.NUMBER.value:
			dct [ 'type' ] = 'number'
		elif _typ == FieldType.FLOAT.value:
			if honour_float:
				dct [ 'type' ] = 'float'
			else:
				dct [ 'type' ] = 'number'
		elif _typ == FieldType.BOOL.value:
			dct [ 'type' ] = 'boolean'
		elif _typ == FieldType.DATE.value:
			dct [ 'type' ] = 'Date'
		elif _typ == FieldType.FILE.value:
			dct [ 'type' ] = 'File'
		elif _typ == FieldType.CUSTOM.value:
			typ = field.type [ 1 ]
			dct [ 'type' ] = typ
			if typ in self.parser.enums:
				dct [ 'type' ] = self.parser.enums [ typ ].name
				dct [ 'type_obj' ] = True
				print ( dct )
				if use_enums: templ = template_obj
			elif typ in self.parser.structures:
				dct [ 'type' ] = self.parser.structures [ typ ].name
				dct [ 'type_obj' ] = True

		if dct [ 'type' ] == 'iliwe':
			dct [ 'type' ] = 'ILiWE'
		elif dct [ 'type' ] == 'ilrequest':
			dct [ 'type' ] = 'ILRequest'
		elif dct [ 'type' ] == 'ilresponse':
			dct [ 'type' ] = 'ILResponse'
		elif dct [ 'type' ] in ( 'date', 'datetime' ):
			dct [ 'type' ] = 'Date'

		if dct [ 'is_array' ]:
			dct [ 'type' ] += '[]'

		if dct [ 'default' ]:
			if dct [ 'type' ].startswith ( 'string' ):
				dct [ '_default' ] = ', default: "%s"' % field.default
			else:
				dct [ '_default' ] = ', default: %s' % field.default
		else:
			dct [ '_default' ] = ''

		if dct [ 'param_default' ]:
			dct [ 'param_default' ] = ' = %s' % dct [ 'param_default' ]
			dct [ 'opt' ] = ''

		if dct [ '_req' ] == 'true':
			dct [ '_req_param' ] = ', required: %(_req)s%(_default)s' % dct
		else:
			dct [ '_req_param' ] = ''


		return templ % dct