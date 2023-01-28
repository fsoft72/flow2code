def type2typescript(typ: str, flow: any = None):
    if typ in ("str", "string", "text"):
        return "string"
    elif typ in ("int", "num", "number", "float"):
        return "number"
    elif typ in ("bool", "boolean", "check", "checkbox"):
        return "boolean"
    elif typ in ("json", "object"):
        return "object"
    elif typ in ("date", "datetime", "time"):
        return "date"
    else:
        if not flow:
            return typ

        if typ in flow.types:
            return flow.types[typ].name
        if typ in flow.enums:
            return flow.enums[typ].name

        return typ
