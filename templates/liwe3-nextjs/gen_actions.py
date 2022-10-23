#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from lib.utils import type2typescript
from texts import texts as TEMPL

# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================

# ==================================================================================================
# CLASS METHODS
# ==================================================================================================
def generate_file_actions ( self, mod: Module, output: str ):
	mod_name = self.mod_name( mod )

	# create the output directory
	outfile = os.path.join( output, "src", "components", mod_name, "core", "actions.ts" )
	fout = self.create_file( outfile, mod )

	fout.write ( TEMPL [ 'ACTIONS_FILE_HEADER' ] % self.snippets )
	self._gen_action_enum ( fout, mod )

	for ep in mod.endpoints.values():
		self._gen_store_fn( fout, ep )

	for ep in mod.endpoints.values():
		self._gen_action( fout, ep )


	# close the output file
	fout.close()
	print( "Generated", outfile )

def _gen_action_enum(self, fout, mod: Module):
	fout.write( TEMPL ['ACTIONS_ENUM_START'])
	for ep in mod.endpoints.values():
		dct = {
			"action_const": self.endpoint_action_name ( ep ).upper(),
			"action_name": self.endpoint_action_name ( ep ),
		}
		fout.write(TEMPL ['ACTION_ENUM'] % dct)

	fout.write(TEMPL['ACTIONS_ENUM_END'])

def _gen_store_fn(self, fout, ep: Endpoint):
	( params, doc ) = self.params_and_doc( ep, TEMPL )

	dct = {
		"action_name": self.endpoint_action_name (ep, 'store_'),
		"action_const": self.endpoint_action_name (ep).upper(),
		"method": ep.method.lower(),
		"url": self.endpoint_action_name(ep).lower(),
		"fields": ', '.join ( ep.fields () ),
		"params": params,
		"return_name": ep.return_name,
		"__doc": doc,
	}

	if dct['fields']: dct['fields'] = ' %(fields)s ' % dct

	if ep.return_name == '__plain__':
		dct['_return_payload'] = '__data'
	else:
		dct['_return_payload'] = '__data.%(return_name)s' % dct

	if dct['params']:
		dct['params'] += ', onsuccess?: any, onerror?: any'
	else:
		dct['params'] = 'onsuccess?: any, onerror?: any'

	fout.write(TEMPL['STORE_FN'] % dct)

def _gen_action (self, fout, ep: Endpoint):
	( params, doc ) = self.params_and_doc( ep, TEMPL, honour_float = False )

	dct = {
		"action_name": self.endpoint_action_name (ep, 'act_'),
		"action_const": self.endpoint_action_name (ep).upper(),
		"store_fn": self.endpoint_action_name(ep, 'store_'),
		"method": ep.method.lower(),
		"url": self.endpoint_action_name(ep).lower(),
		"fields": ', '.join ( ep.fields () ),
		"params": params,
		"return_name": ep.return_name,
		"__doc": doc,
	}

	if dct['fields']: dct['fields'] = ' %(fields)s ' % dct

	if ep.return_name == '__plain__':
		dct['_return_payload'] = '__data'
	else:
		dct['_return_payload'] = '__data.%(return_name)s' % dct

	if dct['params']:
		dct['params'] += 'onsuccess?: any, onerror?: any'
	else:
		dct['params'] = 'onsuccess?: any, onerror?: any'

	fout.write(TEMPL['ACTION_START'] % dct)