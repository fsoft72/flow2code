#!/usr/bin/env python3

# import TemplateBase
from lib.template_base import TemplateBase
from lib.types import Module, Field, FieldType

from gen_types import generate_file_types


class Template(TemplateBase):
    def __init__(self):
        super().__init__()
        self.name = "liwe3-dart"

    def types_and_enums_list(self, mod: Module, *, add_obj=False):
        k = (
            list([x.name for x in mod.types.values()])
            + list([x.name + "Keys" for x in mod.types.values()])
            + list([x.name for x in mod.enums.values()])
        )

        if add_obj:
            k += list([x.name + "Obj" for x in mod.enums.values()])

        k.sort()

        return k

    def code(self, mod: Module, flow: any, output: str):
        super().code(mod, flow, output)
        self.generate_file_types(mod, output)

    def prepare_field(
        self, field: Field, template, template_obj, honour_float=False, use_enums=False
    ):
        dct = {
            "name": field.name,
            "type": "any",
            "type_obj": False,
            "required": field.required,
            "private": field.private,
            "description": field.description,
            "opt": "",
            "param_default": field.default,
            "is_array": field.is_array,
            "default": field.default,
        }

        # The template param holds the default template string to be used
        # it could change if we need to use the _OBJ version of the template
        templ = template

        if dct["param_default"] is None:
            dct["param_default"] = "undefined"

        if dct["required"]:
            dct["_req"] = "true"
            dct["_is_req"] = "req"
            dct["param_default"] = ""
            dct["final"] = "final "
        else:
            dct["opt"] = "?"
            dct["_is_req"] = "opt"
            dct["_req"] = "false"
            dct["final"] = ""

        if dct["private"]:
            dct["private"] = "true"
        else:
            dct["private"] = "false"

        _typ = field.type[0]

        if _typ == FieldType.STR:
            dct["type"] = "String"
            if dct["param_default"] and dct["param_default"] != "undefined":
                dct["param_default"] = '"%s"' % dct["param_default"]
        elif _typ == FieldType.NUMBER:
            dct["type"] = "int"
        elif _typ == FieldType.FLOAT:
            dct["type"] = "float"
        elif _typ == FieldType.BOOL:
            dct["type"] = "bool"
        elif _typ == FieldType.DATE:
            dct["type"] = "Date"
        elif _typ == FieldType.FILE:
            dct["type"] = "File"
        elif _typ == FieldType.CUSTOM:
            typ = field.type[1]
            dct["type"] = typ
            if typ in self.mod.flow.enums:
                dct["type"] = self.mod.flow.enums[typ].name
                dct["type_obj"] = True
                if use_enums:
                    templ = template_obj
            elif typ in self.mod.flow.types:
                dct["type"] = self.mod.flow.types[typ].name
                dct["type_obj"] = True

        if dct["type"] == "iliwe":
            dct["type"] = "ILiWE"
        elif dct["type"] == "ilrequest":
            dct["type"] = "ILRequest"
        elif dct["type"] == "ilresponse":
            dct["type"] = "ILResponse"
        elif dct["type"] in ("date", "datetime"):
            dct["type"] = "Date"

        if dct["is_array"]:
            dct["type"] = "List<%s>" % dct["type"]

        if dct["default"]:
            if dct["type"].startswith("string"):
                dct["_default"] = ', default: "%s"' % field.default
            else:
                dct["_default"] = ", default: %s" % field.default
        else:
            dct["_default"] = ""

        if dct["param_default"]:
            dct["param_default"] = " = %s" % dct["param_default"]
            dct["opt"] = ""

        return templ % dct


# Types.ts file
Template.generate_file_types = generate_file_types
