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
def generate_file_urls ( self, mod: Module, output: str ):
	mod_name = self.mod_name( mod )

	# create the output directory
	outfile = os.path.join( output, "src", "components", mod_name, "core", "urls.ts" )
	fout = self.create_file( outfile, mod )

	fout.write ( TEMPL [ 'URL_START' ] )
	for ep in mod.endpoints.values():
		self._gen_url(fout, ep)

	fout.write ( TEMPL [ 'URL_END' ] )

	# close the output file
	fout.close()
	print( "Generated", outfile )

def _gen_url ( self, fout, ep: Endpoint ):
	dct = {
		"action_name": self.endpoint_action_name ( ep ),
		"path": ep.path,
	}

	fout.write ( TEMPL [ 'URL' ] % dct )
