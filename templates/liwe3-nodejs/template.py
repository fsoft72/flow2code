#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.const import FieldType
from lib.types import Module, Endpoint
from lib.utils import type2typescript

from texts import texts as TEMPL


class Template( TemplateBase ):

	def __init__( self ):
		super().__init__()
		self.name = "liwe3-nodejs"

	def _generate_file_endpoints ( self, mod: Module, output: str ):
		mod_name = self.mod_name( mod )

		# create the output directory
		outfile = os.path.join( output, "server", "modules", mod_name, "endpoints.ts" )
		out = self.create_file( outfile, mod )

		# prepare the methods names
		self._prepare_methods_names ( mod )

		# write the header
		out.write ( TEMPL [ 'HEADER_START' ] % self.snippets )

		for ep in mod.endpoints.values ():
			self._endpoint_definition ( ep, out, mod )

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

	def _endpoint_definition ( self, ep: Endpoint, out, mod: Module ):
		self.mod = mod

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


	def _generate_endpoint ( self, fout, ep: Endpoint ):
		name = self.endpoint_mk_function ( ep )

		params = []
		doc = []
		for p in ep.parameters:
			if p.type == FieldType.FILE: continue
			params.append ( self.prepare_field ( p, TEMPL [ 'EP_TYPED_PARAM' ], '', honour_float = True, use_enums = True ) )
			dct = {
				"name": p.name,
				"doc": p.description,
				"_is_req": "req" if p.required else "opt",
			}
			doc.append ( TEMPL [ 'EP_DOC_FIELD' ] % dct )

		if params:
			params = ', '.join ( params ) + ', '
		else:
			params = ''

		if ep.description:
			description = [ x for x in ep.description.split ( '\n' ) if x.strip() ] + [ '' ] + doc
		else:
			description = doc

		ret_descr = ep.return_description
		if ret_descr:
			ret_descr = " - " + ret_descr
		else:
			ret_descr = ''

		description.append ( "" )
		description.append ( TEMPL [ 'EP_DOC_RETURN' ] % {
			"doc": ret_descr,
			"name": ep.return_name,
			"type": ep.return_type
		})

		description = ' * ' + '\n * '.join ( description ) + '\n *'

		"""
		if doc:
			doc = '\n'.join ( doc )
		else:
			doc = ''
		"""


		dct = {
			"endpoint_name": name,
			"__description": description, # + '\n' +  doc,
			"return_type": type2typescript ( ep.return_type ),
			"__parameters": params,
			"__snippet": self.snippets [ name ],
		}

		if ep.is_array:
			dct [ 'return_type' ] += '[]'

		fout.write ( TEMPL [ 'FOLDING_EP_START' ] % dct )
		fout.write ( TEMPL [ 'EP_START' ] % dct )
		fout.write ( TEMPL [ 'EP_END' ] % dct )
		fout.write ( TEMPL [ 'FOLDING_END' ] % dct )


	def _generate_file_methods ( self, mod: Module, output: str ):
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

		res = []
		res2 = []

		for typ in mod.types.values():
			if typ.coll_table:
				res.append ( TEMPL [ 'TYPE_COLL_VAR' ] % typ.coll_table )
				res2.append ( TEMPL [ 'TYPE_COLL_CONST' ] % ( typ.coll_table.upper(), typ.coll_table ) )

		self.snippets [ "__collections" ] = '\n'.join ( res ) + '\n\n' + '\n'.join ( res2 )

		# write the header
		out.write ( TEMPL [ 'METHODS_FILE_START' ] % self.snippets )

		for ep in mod.endpoints.values ():
			self._generate_endpoint ( out, ep )

		out.write ( TEMPL [ 'METHODS_FILE_END' ] % self.snippets )

		# close the output file
		out.close()

		print( "Generated", outfile )

	def code ( self, mod, output ):
		self._generate_file_endpoints ( mod, output )
		self._generate_file_methods ( mod, output )
