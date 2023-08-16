#!/usr/bin/env python3

texts = {
    "ENUM_START": """/** %(name)s%(description)s */
export enum %(name)s {\n""",
    "ENUM_END": """};\n\n""",
    "ENUM_ROW": """\t/** %(description)s */
\t%(name)s = "%(val)s",\n""",
    "TYPES_START": """// This file is autogenerated by liwe3-svelte
/* eslint-disable @typescript-eslint/no-explicit-any */

/*=== f2c_start __file ===*/
%(__file)s
/*=== f2c_end __file ===*/

""",
    "INTERFACE_START": """/** %(name)s */
export interface %(name)s {
""",
    "INTERFACE_END": """}\n\n""",
    "INTERFACE_PARAM": "	/** %(description)s */\n	%(name)s?: %(type)s;\n",
    "ACTIONS_FILE_HEADER": """/* This file is autogenerated by liwe3-svelte */
/* eslint-disable @typescript-eslint/no-inferrable-types */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
/*=== f2c_start __custom_code ===*/
%(__custom_code)s
/*=== f2c_end __custom_code ===*/
import { get, patch, post, delete_ } from '$liwe3/utils/fetcher';
""",
    "ACTION_START": """
/**
%(__doc)s
 */
export const %(action_name)s = async ( %(params)s ) => {
\treturn await %(method)s( "/api%(url)s", {%(fields)s}, %(_needs_perms)s );
};
""",
    "DOC_PARAM": " * @param %(name)s - %(descr)s",
    "EP_TYPED_PARAM": "%(name)s%(opt)s: %(type)s%(param_default)s",
    "EP_DOC_FIELD": "@param %(name)s - %(doc)s [%(_is_req)s]",
    "EP_DOC_RETURN": "@return %(name)s: %(type)s%(doc)s",
}