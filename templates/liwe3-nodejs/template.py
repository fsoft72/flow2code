#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.const import FieldType

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
		self._prepare_methods_names ( mod )

		out = open( outfile, 'w' )

		# write the header
		out.write ( TEMPL [ 'HEADER_START' ] % self.snippets )

		for ep in mod['endpoints'].values ():
			self._generate_endpoint_code ( ep, out, mod )

		# close the output file
		out.close()
		print( "Generated", outfile )

	def _prepare_methods_names ( self, mod ):
		"""
		prepare the list of all methods for the import { ... } statement
		"""
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

	def _generate_endpoint_code ( self, ep, out, mod ):
		dct = {
			"__method_lower": ep['method'].lower(),
			"url": ep['url'],
			"__endpoint_name": self.endpoint_mk_function ( ep ),
			"__perms": self._perms_get(ep, mod),
			"__typed_dict": '',
			"__params": "params",
		}

		params = [ f [ 'name' ] for f in ep.get ( 'parameters', [] ) if f [ 'type' ] != FieldType.FILE ]

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

		if not ep [ 'permissions' ] or 'public' in ep [ 'permissions' ]: return perms

		if 'logged' in ep [ 'permissions' ]:
			perms = 'perms( [ "is-logged" ] )'
		else:
			perm_names = []
			for k in ep [ 'permissions' ].keys ():
				perm_names.append ( mod [ 'permissions' ].get ( k ) [ 'name' ] )

			perms = 'perms( [ %s ] )' % ( '"' + '", "'.join ( perm_names ) + '"' )

		return perms

	def _typed_dict ( self, ep, dict_name ):
		res = []

		for f in ep.get ( "parameters", [] ):
			#if f [ "type" ] == FieldType.FILE: continue

			dct = self.prepare_field ( f, TEMPL [ 'TYPED_DICT' ], TEMPL [ 'TYPED_DICT_OBJ' ], honour_float = True, use_enums = True )

			res.append ( dct )

		if not res: return ''

		return 'typed_dict( %s, [\n\t\t\t%s\n\t\t] )' % ( dict_name, ',\n\t\t\t'.join ( res ) )

	def code ( self, mod, output ):
		self._generate_endpoint ( mod, output )
