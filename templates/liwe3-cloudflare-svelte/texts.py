#!/usr/bin/env python3

texts = {
    "PACKAGE_JSON": """{
  "name": "@frontend-modules/%(__mod_name)s",
  "version": "0.0.1",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "svelte": "./dist/index.js"
    }
  },
  "files": [
    "dist",
    "!dist/**/*.test.*",
    "!dist/**/*.spec.*"
  ],
  "dependencies": {
    "@frontend/liwe3": "workspace:*"
  },
  "peerDependencies": {
    "@sveltejs/kit": "^2.37.0",
    "svelte": "^5.0.0",
    "svelte-hero-icons": "^5.2.0",
    "zod": "^4.1.11"
  },
  "devDependencies": {
    "@sveltejs/kit": "^2.37.0",
    "@sveltejs/package": "^2.5.0",
    "publint": "^0.3.12",
    "svelte": "^5.38.6",
    "svelte-hero-icons": "^5.2.0",
    "typescript": "^5.9.2",
    "vite": "^7.1.4",
    "vitest": "^3.2.4",
    "zod": "^4.1.11"
  },
  "scripts": {
    "dev": "svelte-package -w -i src --types false",
    "build": "svelte-package -i src && publint",
    "prepublishOnly": "npm run build",
    "test": "vitest"
  }
}
""",
    "TSCONFIG_JSON": """{
  "extends": "../../../tsconfig.json",
  "compilerOptions": {
    "baseUrl": ".",
    "noEmit": true,
    "paths": {
      "@frontend/liwe3": ["../../../@frontend/liwe3/src"],
      "@frontend/liwe3/*": ["../../../@frontend/liwe3/src/*"],
      "@frontend-modules/%(__mod_name)s": ["./src"],
      "@frontend-modules/%(__mod_name)s/*": ["./src/*"]
    }
  },
  "include": [
    "src/**/*.ts",
    "src/**/*.js",
    "src/**/*.svelte"
  ]
}
""",
    "VITEST_CONFIG": """import { defineConfig } from 'vitest/config';

export default defineConfig( {
	test: {
		environment: 'node',
		globals: true
	}
} );
""",
    "ACTIONS_FILE_START": """import { apiClient, type LiWEResponse } from '@frontend/liwe3';

""",
    "INTERNAL_CALL_HELPER": """/**
 * Internal helper function to handle API calls with optional hooks
 * @param method - The API client method to call (e.g., apiClient.get, apiClient.post)
 * @param url - The API endpoint URL
 * @param params - Optional parameters to send with the request
 * @param options - Optional hooks (beforeSend, afterSend, errorHandling)
 * @returns Promise resolving to LiWEResponse
 */
const _internalCall = async <P, R>(
	method: ( url: string, data?: any ) => Promise<any>,
	url: string,
	params?: P,
	options?: LiWEActionOptions
): Promise<LiWEResponse<R>> => {
	// Call beforeSend if defined
	let processedParams = params;

	if ( options?.beforeSend && params !== undefined ) {
		processedParams = await options.beforeSend( params );
	}

	// Make API call
	let res: LiWEResponse<R> = await method( url, processedParams );

	// Check for errors
	if ( !res.ok && options?.errorHandling ) {
		options.errorHandling( res );
		return res;
	}

	// Call afterSend if defined
	if ( options?.afterSend ) {
		res = await options.afterSend( res );
		// Check for errors after afterSend
		if ( !res.ok && options?.errorHandling ) {
			options.errorHandling( res );
			return res;
		}
	}

	return res;
};

""",
}
