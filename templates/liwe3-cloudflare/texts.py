#!/usr/bin/env python3

texts = {
    "INDEX_FILE_START": """import { responseError, type LiWEApp, permissions_register } from '@backend/liwe3/core';
import { type Context } from 'hono';
import { %(__methods)s } from './methods';
import { %(__permissions_const)s } from './perms';

// Module initialization function
export const module_init = ( app: LiWEApp ) => {
	console.log( "=== Module: %(__mod_name)s" );

""",
    "INDEX_FILE_END": """
	// Register %(__mod_name)s module permissions
	permissions_register( {
		module: '%(__mod_name)s',
		perms: %(__permissions_const)s
	} );
};
""",
    "ENDPOINT_GET": """	app.hono.get( '%(__path)s', async ( c: Context ) => {
		const query = c.req.query();
		const res = await %(__method_name)s( app, query as any );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_GET_NO_PARAMS": """	app.hono.get( '%(__path)s', async ( c: Context ) => {
		const res = await %(__method_name)s( app );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_POST": """	app.hono.post( '%(__path)s', async ( c: Context ) => {
		try {
			const %(__param_source)s = await c.req.json();
			const res = await %(__method_name)s( app, %(__param_name)s );
			return c.json( res, res.status );
		} catch ( error ) {
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			return c.json( responseError( errorMessage ) );
		}
	} );

""",
    "ENDPOINT_POST_NO_PARAMS": """	app.hono.post( '%(__path)s', async ( c: Context ) => {
		const res = await %(__method_name)s( app );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_PUT": """	app.hono.put( '%(__path)s', async ( c: Context ) => {
		try {
			const %(__param_source)s = await c.req.json();
			const res = await %(__method_name)s( app, %(__param_name)s );
			return c.json( res, res.status );
		} catch ( error ) {
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			return c.json( responseError( errorMessage ) );
		}
	} );

""",
    "ENDPOINT_PUT_NO_PARAMS": """	app.hono.put( '%(__path)s', async ( c: Context ) => {
		const res = await %(__method_name)s( app );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_PATCH": """	app.hono.patch( '%(__path)s', async ( c: Context ) => {
		try {
			const %(__param_source)s = await c.req.json();
			const res = await %(__method_name)s( app, %(__param_name)s );
			return c.json( res, res.status );
		} catch ( error ) {
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			return c.json( responseError( errorMessage ) );
		}
	} );

""",
    "ENDPOINT_PATCH_NO_PARAMS": """	app.hono.patch( '%(__path)s', async ( c: Context ) => {
		const res = await %(__method_name)s( app );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_DELETE": """	app.hono.delete( '%(__path)s', async ( c: Context ) => {
		const %(__param_source)s = await c.req.json();
		const res = await %(__method_name)s( app, %(__param_name)s );
		return c.json( res, res.status );
	} );

""",
    "ENDPOINT_DELETE_NO_PARAMS": """	app.hono.delete( '%(__path)s', async ( c: Context ) => {
		const res = await %(__method_name)s( app );
		return c.json( res, res.status );
	} );

""",
    "PERMS_FILE_START": """/**
 * @fileoverview %(__mod_name_camel)s Module Permissions
 *
 * Defines all permissions available in the %(__mod_name)s module.
 * These permissions are registered with the global permissions system
 * during module initialization.
 */

import { SystemPermission } from '@backend/liwe3/core';

""",
    "PERMS_CONSTANTS_START": """// Permission constants
""",
    "PERMS_CONST_ROW": """export const %(const_name)s = '%(perm_name)s';
""",
    "PERMS_CONSTANTS_END": """
""",
    "PERMS_ARRAY_START": """/**
 * All permissions available in the %(__mod_name)s module
 */
export const %(__permissions_const)s: SystemPermission[] = [
""",
    "PERMS_FILE_END": """];
""",
    "PERMS_ROW": """	{
		name: %(name)s,
		description: '%(description)s'
	},
""",
    "METHOD_FILE_START": """import { z, LiWEApp, LiWEResponse, responseError, responseSuccess, eq, and, or } from './utils';

""",
    "METHOD_SCHEMA_START": """/**
 * Schema for %(__schema_description)s
 *
%(__schema_properties)s
 */
const %(__schema_name)s = z.object( {
""",
    "METHOD_SCHEMA_FIELD": """	%(name)s: %(zod_type)s,
""",
    "METHOD_SCHEMA_END": """} );

""",
    "METHOD_PARAMS_TYPE": """/** Parameters for %(__function_description)s */
export type %(__params_type)s = z.infer<typeof %(__schema_name)s>;

""",
    "METHOD_RESULT_TYPE": """/** Return type for %(__function_description)s */
export type %(__result_type)s = %(__result_fields)s;

""",
    "METHOD_HEADERS_BLOCK": """/*=== f2c_start %(__block_name)s ===*/
%(__snippet)s
/*=== f2c_end %(__block_name)s ===*/

""",
    "METHOD_FUNCTION_START": """/**
 * %(__function_description)s
 *
%(__param_docs)s *
 * @returns {Promise<LiWEResponse<%(__result_type)s>>} Result object with success status and data or error details
 */
export const %(__function_name)s = async ( app: LiWEApp%(__params_arg)s ): Promise<LiWEResponse<%(__result_type)s>> => {
""",
    "METHOD_VALIDATION": """	const validation = %(__schema_name)s.safeParse( params );
	if ( !validation.success ) {
		return responseError( validation.error.message, 400, 'VALIDATION_ERROR' );
	}

""",
    "METHOD_PARAMS_EXTRACT": """	const { %(__param_names)s } = validation.data;

""",
    "METHOD_BODY_BLOCK": """	/*=== f2c_start %(__block_name)s ===*/
%(__snippet)s
	/*=== f2c_end %(__block_name)s ===*/
""",
    "METHOD_FUNCTION_END": """};
""",
    "METHOD_UTILS_FILE": """/**
 * @fileoverview Common utilities for %(__mod_name)s module methods
 */

// Core imports
export { LiWEApp, LiWEResponse, responseError, responseSuccess } from '@backend/liwe3/core';

// Database operation imports
export { eq, and, ne, desc, asc, count, avg, sql, inArray, or, like, isNull } from 'drizzle-orm';

// Schema imports
// TODO: Import your schema tables here

// Zod for validation
export { z } from 'zod';

/*=== f2c_start utils ===*/
%(__utils_snippet)s
/*=== f2c_end utils ===*/
""",
    "METHODS_INDEX_START": """/**
 * @fileoverview Re-exports all %(__mod_name)s methods and types
 */

""",
    "METHODS_INDEX_EXPORT": """export { %(__function_name)s, type %(__params_type)s, type %(__result_type)s } from './%(__file_name)s';
""",
    "METHODS_WRAPPER_FILE": """/**
 * @fileoverview %(__mod_name_camel)s Module Methods - Re-exports from individual method files
 *
 * This file maintains backward compatibility by re-exporting all methods
 * from their individual files in the methods/ directory.
 */

// Re-export all methods and types from the methods directory
export * from './methods/index';
""",
    "SCHEMA_FILE_START": """import { relations, sql } from 'drizzle-orm';
import { text, integer, sqliteTable, index, real, uniqueIndex } from 'drizzle-orm/sqlite-core';

""",
    "SCHEMA_FILE_END": "",
    "SQL_FILE_HEADER": """-- SQL Schema for %(__mod_name)s module
-- Generated by flow2code
-- Database: SQLite

""",
    "PACKAGE_JSON": """{
  "name": "@backend/modules/%(__mod_name)s",
  "version": "1.0.0",
  "description": "%(__mod_name_camel)s module",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {
    "@backend/liwe3/core": "workspace:*",
    "drizzle-orm": "^0.44.5",
    "zod": "^4.1.3"
  },
  "devDependencies": {
    "@types/node": "^22.10.5",
    "@vitest/ui": "^3.2.4",
    "hono": "^4.9.5",
    "typescript": "^5.9.2",
    "vitest": "^2.1.8"
  }
}
""",
    "TSCONFIG_JSON": """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "allowJs": true,
    "strict": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": [
    "src/**/*"
  ],
  "exclude": [
    "node_modules",
    "dist"
  ]
}
""",
    "VITEST_CONFIG": """import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
	resolve: {
		alias: {
			'@backend/liwe3/core/src/crypto': path.resolve(__dirname, '../../../@backend/liwe3/core/src/crypto.ts'),
			'@backend/liwe3/core': path.resolve(__dirname, '../../../@backend/liwe3/core/src/index.ts')
		}
	},
	test: {
		environment: 'node',
		globals: true,
		include: ['tests/**/*.test.ts'],
		coverage: {
			reporter: ['text', 'json', 'html'],
			include: ['src/**/*.ts'],
			exclude: ['src/**/*.d.ts']
		}
	}
});
""",
}
