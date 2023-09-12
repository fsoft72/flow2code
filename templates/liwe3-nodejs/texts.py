#!/usr/bin/env python3

texts = {
    "HEADER_START": """/*
 * This file has been generated by flow2code
 * See: https://flow.liwe.org
 */

import { ILRequest, ILResponse, ILError, ILiWE } from '../../liwe/types';
import { send_error, send_ok, typed_dict } from "../../liwe/utils";
import { locale_load } from '../../liwe/locale';

import { perms } from '../../liwe/auth';

import {
\t// endpoints function
\t%(__methods)s
\t// functions
\t%(__functions)s
} from './methods';

import {
\t%(__interfaces)s
} from './types';

/*=== f2c_start __header ===*/
%(__header)s
/*=== f2c_end __header ===*/

export const init = ( liwe: ILiWE ) => {
\tconst app = liwe.app;

\tconsole.log( "    - %(__name_camel)s " );

\tliwe.cfg.app.languages.map( ( l ) => locale_load( "%(__name_lower)s", l ) );
\t%(__name_lower)s_db_init ( liwe );
""",
    "HEADER_END": """
};
""",
    "ENDPOINT": """
\tapp.%(__method_lower)s ( '/api%(url)s', %(__perms)s( req: ILRequest, res: ILResponse ) => {
\t\t%(__typed_dict)s

\t\t%(__endpoint_name)s ( req, %(__full_params)s( err: ILError, %(__return_var_name)s: %(__return_type)s ) => {
\t\t\tif ( err ) return send_error( res, err );

\t\t\tsend_ok( res, { %(__spread)s%(__return_var_name)s } );
\t\t} );
\t} );
""",
    "TYPED_DICT": '{ name: "%(name)s", type: "%(type)s"%(_req_param)s }',
    "TYPED_DICT_OBJ": '{ name: "%(name)s", type: %(type)sObj%(_req_param)s }',
    "METHODS_FILE_START": """/*
 * This file has been generated by flow2code
 * See: https://flow.liwe.org
 */

import { ILRequest, ILResponse, LCback, ILiweConfig, ILError, ILiWE } from '../../liwe/types';
import { $l } from '../../liwe/locale';
%(__import_system_perms_register)s
import {
\t%(__interfaces)s
} from './types';

import _module_perms from './perms';

let _liwe: ILiWE = null;

const _ = ( txt: string, vals: any = null, plural = false ) => {
\treturn $l( txt, vals, plural, "%(__name_lower)s" );
};

%(__collections)s

/*=== f2c_start __file_header === */
%(__file_header)s
/*=== f2c_end __file_header ===*/

""",
    "METHODS_FILE_END": """\n""",
    "TYPE_COLL_VAR": "let _coll_%s: DocumentCollection = null;",
    "TYPE_COLL_CONST": 'const COLL_%s = "%s";',
    "FOLDING_EP_START": """// {{{ %(endpoint_name)s ( req: ILRequest, %(__parameters)scback: LCBack = null ): Promise<%(return_type)s>""",  # noqa
    "FOLDING_FN_START": """// {{{ %(function_name)s ( %(__parameters)scback: LCBack = null ): Promise<%(return_type)s>""",  # noqa
    "FOLDING_END": """// }}}\n\n""",
    "EP_TYPED_PARAM": "%(name)s%(opt)s: %(type)s%(param_default)s",
    "EP_DOC_FIELD": "@param %(name)s - %(doc)s [%(_is_req)s]",
    "EP_DOC_RETURN": "@return %(name)s: %(return_type)s%(doc)s",
    "DB_INDEX": """{ type: "%(_type)s", fields: [ "%(_name)s" ], unique: %(_unique)s },""",
    # "COLL_DEF": """%(coll_name)s = await adb_collection_init( liwe.db, %(table_name)s, [\n\t\t\t%(rows)s\n\t\t], %(coll_drop)s );\n""",  # noqa
    "COLL_DEF": """await adb_collection_init( liwe.db, %(table_name)s, [\n\t\t\t%(rows)s\n\t\t], %(coll_drop)s );\n""",  # noqa
    "EP_START": """
/**
 *
%(__description)s
 */
export const %(endpoint_name)s = ( req: ILRequest, %(__parameters)scback: LCback = null ): Promise<%(return_type)s> => {
\treturn new Promise( async ( resolve, reject ) => {
\t\t/*=== f2c_start %(endpoint_name)s ===*/
%(__snippet)s""",
    "EP_END": """
\t\t/*=== f2c_end %(endpoint_name)s ===*/
\t} );
};
""",
    "FUNCTION_START": """
/**
 *
%(__description)s
 */
export const %(function_name)s = ( %(__parameters)scback: LCback = null ): Promise<%(return_type)s> => {
\treturn new Promise( async ( resolve, reject ) => {
%(__pre_snip)s		/*=== f2c_start %(function_name)s ===*/
%(__snippet)s
""",
    "FUNCTION_END": """		/*=== f2c_end %(function_name)s ===*/
\t} );
};
""",
    "TYPES_FILE_START": """/* Types file generated by flow2code */

/*=== f2c_start __file ===*/
%(__file)s
/*=== f2c_end __file ===*/
""",
    "TYPES_FILE_END": "",
    "PERMS_FILE_START": """/* Permissions file generated by flow2code */

/*=== f2c_start __file ===*/
%(__file)s
/*=== f2c_end __file ===*/

const permissions = {
""",
    "PERMS_FILE_END": """};

export default permissions;
""",
    "PERMS_ROW": """\t"%(name)s": "%(description)s",\n""",
    "ENUM_START": """/** %(name)s%(description)s */
export enum %(name)s {\n""",
    "ENUM_END": """};\n\n""",
    "ENUM_ROW": """\t/** %(description)s */
\t%(name)s = "%(val)s",\n""",
    "ENUM_OBJ_START": """export const %(name)sObj = {
\t__name: "%(name)s",\n""",
    "ENUM_OBJ_END": """};\n\n""",
    "ENUM_OBJ_ROW": """\t%(name)s: "%(val)s",\n""",
    "INTERFACE_START": """/** %(name)s */
export interface %(name)s {
""",
    "INTERFACE_END": """}\n\n""",
    "INTERFACE_KEYS_START": """export const %(name)sKeys = {
""",
    "INTERFACE_KEYS_END": """};\n\n""",
    "INTERFACE_PARAM": "	/** %(description)s */\n	%(name)s%(opt)s: %(type)s;\n",
    "INTERFACE_PARAM_NO_DESCR": "	%(name)s?: %(type)s;\n",
    "INTERFACE_KEY_PARAM": "	'%(name)s': { type: '%(type)s', priv: %(private)s },\n",
}
