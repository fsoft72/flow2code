def type2typescript ( typ: str ):
	if typ in ( 'str', 'string', 'text' ):
		return 'string'
	elif typ in ( 'int', 'num', 'number', 'float' ):
		return 'number'
	elif typ in ( 'bool', 'boolean', 'check', 'checkbox' ):
		return 'boolean'
	elif typ in ( 'json', 'object' ):
		return 'object'
	elif typ in ( 'date', 'datetime', 'time' ):
		return 'date'
	else:
		return typ
