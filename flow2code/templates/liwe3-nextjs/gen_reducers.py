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
def generate_file_reducer ( self, mod: Module, output: str ):
	mod_name = self.mod_name( mod )

	# create the output directory
	outfile = os.path.join( output, "src", "modules", mod_name, "core", "reducer.ts" )
	fout = self.create_file( outfile, mod )

	fout.write ( TEMPL [ 'REDUCERS_START' ] % self.snippets )
	fout.write ( TEMPL [ 'REDUCERS_END' ] % self.snippets )

	# close the output file
	fout.close()
	print( "Generated", outfile )
