import re


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


def camel2snake(name: str):
    s = re.sub(r"([A-Z])", r"_\1", name).lower()

    # remove the first _ if it is the first character
    if s[0] == "_":
        s = s[1:]

    # all lower case
    s = s.lower()

    # if there are situations like a_b_ciao convert it to ab_ciao
    s = re.sub(r"[^a-z]*([a-z])_([a-z])_", r"\1\2_", s)

    return s
