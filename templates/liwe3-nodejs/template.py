#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.const import FieldType
from lib.types import Module, Endpoint

from texts import texts as TEMPL


class Template( TemplateBase ):

	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nodejs"

	def _generate_endpoint ( self, mod: Module, output: str ):
		mod_name = self.mod_name( mod )

		# create the output directory
		outfile = os.path.join( output, "server", "modules", mod_name, "endpoints.ts" )
		out = self.create_file( outfile, mod )

		# prepare the methods names
		self._prepare_methods_names ( mod )

		# write the header
		out.write ( TEMPL [ 'HEADER_START' ] % self.snippets )

		for ep in mod.endpoints.values ():
			self._generate_endpoint_code ( ep, out, mod )

		out.write ( TEMPL [ 'HEADER_END' ] % self.snippets )

		# close the output file
		out.close()
		print( "Generated", outfile )

	def _prepare_methods_names ( self, mod ):
		"""
		prepare the list of all methods for the import { ... } statement
		"""
		# prepare the methods
		methods = []
		for ep in mod.endpoints.values():
			name = self.endpoint_mk_function ( ep )
			methods.append( name )

		# sort the methods
		methods.sort()

		self.snippets[ '__methods' ] = self.join_newlines( methods )

	def _generate_endpoint_code ( self, ep: Endpoint, out, mod: Module ):
		dct = {
			"__method_lower": ep.method.lower(),
			"url": ep.path,
			"__endpoint_name": self.endpoint_mk_function ( ep ),
			"__perms": self._perms_get(ep, mod),
			"__typed_dict": '',
			"__params": "",
		}

		#params = [ f [ 'name' ] for f in ep.get ( 'parameters', [] ) if f [ 'type' ] != FieldType.FILE ]
		params = ep.fields( skip_file_fields= True )

		if params:
			dct [ '__params' ] = ', '.join ( params ) + ', '

		if dct [ '__perms' ]:
			dct [ '__perms' ] += ', '

		m = dct [ '__method_lower' ]
		if m in ( 'post', 'patch', 'put', 'delete' ):
			dct [ 'req_mode' ] = 'req.body'
		elif m == 'get':
			if dct [ 'url'  ].find ( ":" ) == -1:
				dct [ 'req_mode' ] = 'req.query as any'
			else:
				dct [ 'req_mode' ] = 'req.params'

		dct [ '__typed_dict' ] = self._typed_dict ( ep, dct [ 'req_mode' ] )

		if dct [ '__typed_dict' ]:
			dct [ '__typed_dict' ] = "const { %s___errors } = %s;\n\n\t\tif ( ___errors.length ) return send_error ( res, { message: `Parameters error: ${___errors.join ( ', ' )}` } );" %  ( dct [ '__params' ], dct [ '__typed_dict' ] )


		# write the endpoint code
		out.write ( TEMPL [ 'ENDPOINT' ] % dct )

	def _perms_get ( self, ep, mod ):
		perms = ''

		if not ep.permissions or 'public' in ep.permissions: return perms

		if 'logged' in ep.permissions:
			perms = 'perms( [ "is-logged" ] )'
		else:
			"""
			print ( "=== PERMS: ", ep.permissions )
			for k in ep.permissions:
				perm_names.append ( mod [ 'permissions' ].get ( k ) [ 'name' ] )
			"""

			perms = 'perms( [ %s ] )' % ( '"' + '", "'.join ( ep.permissions ) + '"' )

		return perms

	def _typed_dict ( self, ep, dict_name ):
		res = []

		for f in ep.parameters:
			#if f [ "type" ] == FieldType.FILE: continue

			dct = self.prepare_field ( f, TEMPL [ 'TYPED_DICT' ], TEMPL [ 'TYPED_DICT_OBJ' ], honour_float = True, use_enums = True )

			res.append ( dct )

		if not res: return ''

		return 'typed_dict( %s, [\n\t\t\t%s\n\t\t] )' % ( dict_name, ',\n\t\t\t'.join ( res ) )

	def _generate_methods ( self, mod: Module, output: str ):
		"""
		generate the methods.ts file
		"""
		mod_name = self.mod_name( mod )

		# create the output directory
		outfile = os.path.join( output, "server", "modules", mod_name, "methods.ts" )
		out = self.create_file( outfile, mod )

		k = list ( [ x.name for x in mod.types.values () ] ) + list ( [ x.name + "Keys" for x in mod.types.values () ] ) +  list ( [ x.name for x in mod.enums.values () ] )
		k.sort ()
		self.snippets [ "__interfaces" ] = self.join_newlines(k)

		# write the header
		out.write ( TEMPL [ 'METHODS_FILE_START' ] % self.snippets )

		"""
		for ep in mod.endpoints.values ():
			self._generate_endpoint_code ( ep, out, mod )
		"""

		out.write ( TEMPL [ 'METHODS_FILE_END' ] % self.snippets )

		# close the output file
		out.close()

		print( "Generated", outfile )

	def code ( self, mod, output ):
		self._generate_endpoint ( mod, output )
		self._generate_methods ( mod, output )
