#!/usr/bin/env python3

texts = {
	"ENUM_START": """/** %(name)s%(description)s */
export enum %(name)s {\n""",
	"ENUM_END": """};\n\n""",
	"ENUM_ROW": """\t/** %(description)s */
	%(name)s = "%(val)s",\n""",

	"INTERFACE_START": """/** %(name)s */
export interface %(name)s {
""",
	"INTERFACE_END": """}\n\n""",
	"INTERFACE_PARAM": "	/** %(description)s */\n	%(name)s?: %(type)s;\n",
	"URL_START": """/* WARNING: auto generated file  DO NOT EDIT */

import { Actions } from './actions';

const urls = {
""",
	"URL": '\t%(action_name)s: () => `${ process.env.NEXT_PUBLIC_API_SERVER }%(path)s`,\n',
	"URL_END": "};\nexport default urls;\n",
	"ACTIONS_FILE_HEADER": """/*=== d2r_start __custom_code ===*/
%(__custom_code)s
/*=== d2r_end __custom_code ===*/

import liweUseFetch from "@liwe3/hooks/use_fetch";
import urls from './urls';

const fetch = liweUseFetch();

const _has_error = ( u: string, res: any, __data: any ) => {
	if ( !res.ok ) {
		console.log( "ERROR: ", res, __data );
		const msg = __data?.error?.message || res.statusText;
		fetch.error( u, msg, res.status );
		return true;
	}
};
""",
	"STORE_FN": """
export const %(action_name)s = ( dispatch: any, payload: any ) => dispatch && dispatch( { type: Actions.%(action_const)s, payload } );""",
	"ACTION_START": """
/**
%(__doc)s
 */
export const %(action_name)s = ( %(params)s ) => async ( dispatch: any = null ) => {
	const u = urls.%(url)s();
	return fetch.%(method)s( u, {%(fields)s} )
		.catch( ( err ) => console.error( "CRITICAL ERROR: ", err ) )
		.then( async ( res: any ) => {
			const __data = await res.json();

			if ( _has_error( u, res, __data ) ) return;

			dispatch && %(store_fn)s ( dispatch, %(_return_payload)s );
			onsuccess && onsuccess( %(_return_payload)s );

			return %(_return_payload)s;
		} )
		.catch( ( err ) => { onerror && onerror( err ); } );
};
""",
	"ACTIONS_ENUM_START": """
export enum Actions {
""",
	"ACTION_ENUM": "\t%(action_const)s = '%(action_name)s',\n",
	"ACTIONS_ENUM_END": """
};
""",
	"PERM_ROW": """	"%(name)s": "%(description)s",""",
	"REDUCER_STATE": """/* define here the reducer state for %(module_name)s */

/*=== d2r_start _import ===*/
%(_import)s
/*=== d2r_end _import ===*/
import dynamic from 'next/dynamic';

import system_menu, { system_paths } from '@LiWEComponents/system/menu';
import system_perms from '@LiWEComponents/system/perms';

system_menu[ '%(module_name)s' ] = [
	%(_menus)s
];

system_perms[ '%(module_name_low)s' ] = {
	"admin": "Completely admin module %(module_name)s",
%(_perms)s
};

/*=== d2r_start _system_paths ===*/
%(_system_paths)s
/*=== d2r_end _system_paths ===*/


export interface %(module_name)sState {
	/*=== d2r_start __state ===*/
%(__state)s
	/*=== d2r_end __state ===*/
};

const initial_state: %(module_name)sState = {
	/*=== d2r_start __initial_state ===*/
%(__initial_state)s
	/*=== d2r_end __initial_state ===*/
};

export default initial_state;
""",
	"DOC_PARAM": " * @param %(name)s - %(descr)s",
	"EP_TYPED_PARAM": "%(name)s%(opt)s: %(type)s%(param_default)s",
	"EP_DOC_FIELD": "@param %(name)s - %(doc)s [%(_is_req)s]",
	"EP_DOC_RETURN": "@return %(name)s: %(type)s%(doc)s",
	"REDUCERS_START": """/*=== d2r_start __custom_code ===*/
%(_snippet)s
/*=== d2r_end __custom_code ===*/

import { Actions } from './actions';
import { ReduxFunctions } from '../reducer_functions';
import initialState, { %(module_name)sState } from '../initial_state';

interface ActionPayload {
	type: string;
	payload: any;
};

const reducer = ( state = initialState, action: ActionPayload ): %(module_name)sState => {
	const new_state = { ...state };
	const fn = ReduxFunctions[ action.type ];

	if ( ! fn ) {
		console.log( "WARNING: unknown action type: ", action.type );
		return state;
	}

	return fn( new_state, action.payload );
};
""",
	"REDUCERS_END": """

export default reducer;
""",
}