#!/usr/bin/env python3

# import TemplateBase
import os
from lib.template_base import TemplateBase
from lib.const import FieldType
from lib.types import Module, Endpoint, Function, Enum, Type
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

		k = self._types_and_enums_list( mod, add_obj = True )
		self.snippets [ "__interfaces" ] = self.join_newlines(k)

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

		# prepare the functions
		functions = []
		for fn in mod.functions.values():
			functions.append( fn.name )

		# sort the functions
		functions.sort()

		self.snippets[ '__methods' ] = self.join_newlines( methods )
		self.snippets[ '__functions' ] = self.join_newlines( functions )

	def _endpoint_definition ( self, ep: Endpoint, out, mod: Module ):
		self.mod = mod

		dct = {
			"__method_lower": ep.method.lower(),
			"url": ep.path,
			"__endpoint_name": self.endpoint_mk_function ( ep ),
			"__perms": self._perms_get(ep, mod),
			"__typed_dict": '',
			"__params": "",
			"__return_var_name": ep.return_name,
			"__return_type": type2typescript ( ep.return_type, self.mod.flow ),
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

	def _perms_get ( self, ep: Endpoint, mod: Module ) -> str:
		perms = ''

		if not ep.permissions or 'public' in ep.permissions: return perms

		if 'logged' in ep.permissions:
			perms = 'perms( [ "is-logged" ] )'
		else:
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
			params.append ( self.prepare_field ( p, TEMPL [ 'EP_TYPED_PARAM' ], TEMPL [ 'EP_TYPED_PARAM' ], honour_float = False, use_enums = True ) )
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

		documentation = self.mk_documentation( ep.description, doc, ep.return_name, ep.return_type, ep.return_description, TEMPL )

		dct = {
			"endpoint_name": name,
			"__description": documentation,
			"return_type": type2typescript ( ep.return_type, self.mod.flow ),
			"__parameters": params,
			"__snippet": self.snippets [ name ],
		}

		if ep.is_array:
			dct [ 'return_type' ] += '[]'

		fout.write ( TEMPL [ 'FOLDING_EP_START' ] % dct )
		fout.write ( TEMPL [ 'EP_START' ] % dct )
		fout.write ( TEMPL [ 'EP_END' ] % dct )
		fout.write ( TEMPL [ 'FOLDING_END' ] % dct )

	def _gen_db_init ( self, ep: Endpoint, mod: Module, TEMPL: dict[str, str] ):
		res = [ "\t\t_liwe = liwe;\n" ]

		DB_INDEX = TEMPL [ 'DB_INDEX' ]

		for k, v in mod.types.items ():
			coll = []
			if not v.coll_table: continue

			for f in v.fields:
				idx = ''
				if f.idx_unique:
					idx = DB_INDEX % ( { "_unique": 'true', "_name": f.name, "_type": "persistent" } )
				elif f.idx_multi:
					idx = DB_INDEX % ( { "_unique": 'false', "_name": f.name, "_type": "persistent" } )
				elif f.idx_array:
					idx = DB_INDEX % ( { "_unique": 'false', "_name": f.name + "[*]", "_type": "persistent" } )
				elif f.idx_fulltext:
					idx = DB_INDEX % ( { "_unique": 'false', "_name": f.name, "_type": "fulltext" } )

				if not idx: continue

				coll.append ( idx )

			if coll:
				dct = {
					"coll_name": '_coll_%s' % v.coll_table,
					"table_name": 'COLL_' + v.coll_table.upper (),
					"rows": '\n\t\t\t'.join ( coll )
				}

				if v.coll_drop:
					dct [ 'coll_drop' ] = '{ drop: true }'
				else:
					dct [ 'coll_drop' ] = '{ drop: false }'

				res.append ( TEMPL [ 'COLL_DEF' ] % dct )

		return '\n\t\t'.join ( res ) + "\n"

	def _gen_enum ( self, fout, enum: Enum ):
		keys = sorted ( list ( enum.consts.keys () ) )

		dct = { "name": enum.name, "description": enum.description }

		if dct [ 'description' ]:
			dct [ 'description' ] = ' - ' + dct [ 'description' ]

		fout.write ( TEMPL [ 'ENUM_START' ] % dct )
		for k in keys:
			v = enum.consts [ k ]
			d = { "name": k, "val": v [ 'name' ], "description": v [ 'description' ] }
			fout.write ( TEMPL [ 'ENUM_ROW' ] % d )

		fout.write ( TEMPL [ 'ENUM_END' ] % dct )

		fout.write ( TEMPL [ 'ENUM_OBJ_START' ] % dct )
		for k in keys:
			v = enum.consts [ k ]
			d = { "name": k, "val": v [ 'name' ] }
			fout.write ( TEMPL [ 'ENUM_OBJ_ROW' ] % d )

		fout.write ( TEMPL [ 'ENUM_OBJ_END' ] % dct )

	def _gen_type ( self, fout, typ: Type ):
		dct = { "name": typ.name }

		fout.write ( TEMPL [ 'INTERFACE_START' ] % dct )
		for f in typ.fields:
			fout.write ( self.prepare_field(f, TEMPL [ 'INTERFACE_PARAM' ], '' ) )
		fout.write ( TEMPL [ 'INTERFACE_END' ] )

		fout.write ( TEMPL [ 'INTERFACE_KEYS_START' ] % dct )
		for f in typ.fields:
			fout.write ( self.prepare_field(f, TEMPL [ 'INTERFACE_KEY_PARAM' ], '' ) )
		fout.write ( TEMPL [ 'INTERFACE_KEYS_END' ] )

	def _generate_function ( self, fout, fn: Function, mod: Module, ep: Endpoint ):
		name = fn.name

		params = []
		doc = []
		for p in fn.parameters:
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

		params, documentation = self.params_and_doc( fn, TEMPL)

		dct = {
			"function_name": name,
			"__description": documentation,
			"return_type": type2typescript ( fn.return_type, self.mod.flow ),
			"__parameters": params,
			"__snippet": self.snippets [ name ],
			"__pre_snip": "",
		}

		if fn.is_array:
			dct [ 'return_type' ] += '[]'

		if name.endswith ( "_db_init" ):
			dct [ '__pre_snip' ] = self._gen_db_init ( ep, mod, TEMPL )

		fout.write ( TEMPL [ 'FOLDING_FN_START' ] % dct )
		fout.write ( TEMPL [ 'FUNCTION_START' ] % dct )
		fout.write ( TEMPL [ 'FUNCTION_END' ] % dct )
		fout.write ( TEMPL [ 'FOLDING_END' ] % dct )

	def _types_and_enums_list ( self, mod: Module, *, add_obj = False ):
		k = list ( [ x.name for x in mod.types.values () ] ) + list ( [ x.name + "Keys" for x in mod.types.values () ] ) +  list ( [ x.name for x in mod.enums.values () ] )

		if add_obj:
			k += list ( [ x.name + "Obj" for x in mod.enums.values () ] )

		k.sort ()

		return k

	def _generate_file_methods ( self, mod: Module, output: str ):
		"""
		generate the methods.ts file
		"""
		mod_name = self.mod_name( mod )

		# create the output directory
		outfile = os.path.join( output, "server", "modules", mod_name, "methods.ts" )
		out = self.create_file( outfile, mod )

		k = self._types_and_enums_list( mod)
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

		for fn in mod.functions.values():
			self._generate_function ( out, fn, mod, ep )

		out.write ( TEMPL [ 'METHODS_FILE_END' ] % self.snippets )

		# close the output file
		out.close()

		print( "Generated", outfile )

	def _generate_file_types ( self, mod: Module, output: str ):
		"""
		generate the methods.ts file
		"""
		mod_name = self.mod_name( mod )

		# create the output directory
		outfile = os.path.join( output, "server", "modules", mod_name, "types.ts" )
		out = self.create_file( outfile, mod )

		for ep in mod.enums.values ():
			self._gen_enum ( out, ep )

		for ep in mod.types.values ():
			self._gen_type ( out, ep )


		out.write ( TEMPL [ 'TYPES_FILE_END' ] % self.snippets )
		# close the output file
		out.close()

		print( "Generated", outfile )


	def code ( self, mod, output ):
		self._generate_file_endpoints ( mod, output )
		self._generate_file_methods ( mod, output )
		self._generate_file_types ( mod, output )
