#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from lib.utils import type2typescript
from texts import texts as TEMPL

# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================

def _perms_get ( ep: Endpoint, mod: Module ) -> str:
	perms = ''

	if not ep.permissions or 'public' in ep.permissions: return perms

	if 'logged' in ep.permissions:
		perms = 'perms( [ "is-logged" ] )'
	else:
		perms = 'perms( [ %s ] )' % ( '"' + '", "'.join ( ep.permissions ) + '"' )

	return perms

# ==================================================================================================
# CLASS METHODS
# ==================================================================================================
def generate_file_endpoints ( self, mod: Module, output: str ):
	mod_name = self.mod_name( mod )

	# create the output directory
	outfile = os.path.join( output, "server", "modules", mod_name, "endpoints.ts" )
	out = self.create_file( outfile, mod )

	# prepare the methods names
	self._prepare_methods_names ( mod )

	k = self.types_and_enums_list( mod, add_obj = True )
	self.snippets [ "__interfaces" ] = self.join_newlines(k)

	# write the header
	out.write ( TEMPL [ 'HEADER_START' ] % self.snippets )

	for ep in mod.endpoints.values ():
		self._endpoint_definition ( ep, out, mod )

	out.write ( TEMPL [ 'HEADER_END' ] % self.snippets )

	# close the output file
	out.close()
	print( "Generated", outfile )

def _endpoint_definition ( self, ep: Endpoint, out, mod: Module ):
	self.mod = mod

	dct = {
		"__method_lower": ep.method.lower(),
		"url": ep.path,
		"__endpoint_name": self.endpoint_mk_function ( ep ),
		"__perms": _perms_get(ep, mod),
		"__typed_dict": '',
		"__params": "",
		"__return_var_name": ep.return_name,
		"__return_type": type2typescript ( ep.return_type, self.mod.flow ),
		"__spread": "",
	}

	#params = [ f [ 'name' ] for f in ep.get ( 'parameters', [] ) if f [ 'type' ] != FieldType.FILE ]
	params = ep.fields( skip_file_fields= False )

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

	if dct [ '__return_var_name' ] == '__plain__':
		dct [ '__spread' ] = '...'

	# write the endpoint code
	out.write ( TEMPL [ 'ENDPOINT' ] % dct )

def _prepare_methods_names ( self, mod: Module ):
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

def _typed_dict ( self, ep, dict_name ):
	res = []

	for f in ep.parameters:
		#if f [ "type" ] == FieldType.FILE: continue

		dct = self.prepare_field ( f, TEMPL [ 'TYPED_DICT' ], TEMPL [ 'TYPED_DICT_OBJ' ], honour_float = True, use_enums = True )

		res.append ( dct )

	if not res: return ''

	return 'typed_dict( %s, [\n\t\t\t%s\n\t\t] )' % ( dict_name, ',\n\t\t\t'.join ( res ) )


