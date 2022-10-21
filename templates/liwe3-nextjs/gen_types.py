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
def generate_file_types ( self, mod: Module, output: str ):
	mod_name = self.mod_name( mod )

	# create the output directory
	outfile = os.path.join( output, "src", "components", mod_name, "core", "types.ts" )
	out = self.create_file( outfile, mod )

	# close the output file
	out.close()
	print( "Generated", outfile )