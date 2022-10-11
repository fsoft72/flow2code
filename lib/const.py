#!/usr/bin/env python3
from enum import Enum

class FieldType ( Enum ):
	NONE = "none"
	STR = "str"
	NUMBER = "num"
	FLOAT = "float"
	BOOL = "bool"
	OBJECT = "obj"
	DATE = "date"
	DATETIME = "datetime"
	TIME = "time"
	MULTI = "multi"	# Can be multiple types at once (eg. str | num )
	FILE = "file"
	CUSTOM = "custom"