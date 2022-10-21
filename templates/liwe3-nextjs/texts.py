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
}