#!/usr/bin/env python3

import json
import re
from .const import FieldType


class Field:
    ...


class Module:
    ...


class Type:
    ...


class Permission:
    ...


class Function:
    id: str = ""
    name = None
    parameters = []
    return_type = None
    return_description = None
    return_name = None
    is_array = False

    def __init__(self, json_data, mod: Module):
        self.mod = Module
        self.is_valid = False

        self.id = json_data["id"]
        self.name = json_data["name"]
        self.return_type = json_data["returnType"]
        self.return_name = json_data.get("returnName", "")
        self.is_array = json_data.get("is_array", False)
        self.description = json_data["description"]
        self.parameters = []

        for par in json_data["parameters"]:
            f = Field(par, mod)
            self.parameters.append(f)

    def dump(self, indent_size):
        indent = " " * indent_size
        print("\n%s%s" % (indent, self))
        print("%s    Parameters" % indent)
        for p in self.parameters:
            print("%s        %s" % (indent, p))

    def fields(self):
        return [p.name for p in self.parameters]

    def __str__(self):
        return "%s [%s]" % (self.name, self.return_type)


class Enum:
    id: str = ""
    name: str = ""
    description: str = ""
    consts: dict[str, str] = {}

    def __init__(self, json_data, mod: Module):
        self.consts = {}
        self.id = json_data["id"]
        self.name = json_data["name"]
        self.description = json_data.get("description", "")
        self.consts = {}

        for v in json_data["fields"]:
            self.consts[v["name"]] = {
                "name": v["name"].lower(),
                "description": v["description"],
            }

        mod.flow.enums[self.id] = self

    def __str__(self):
        dct = {"name": self.name, "consts": self.consts.keys()}
        return "Enum: %(name)s [%(consts)s]" % dct


class Field:  # noqa
    id: str = ""
    name: str = ""
    type = FieldType.NONE
    required: bool = False
    description: str = ""
    default: str = ""
    types = []
    private: bool = False
    is_array: bool = False
    idx_unique: bool = False
    idx_multi: bool = False
    idx_array: bool = False
    idx_fulltext: bool = False

    def __init__(self, json_data, mod: any):
        self.id = json_data.get("id", "")
        self.name = json_data.get("name", "")
        self.type = self._get_type(json_data.get("type", {}))
        self.required = json_data.get("required", False)
        self.is_array = json_data.get("is_array", False)
        self.description = json_data.get("description", "")
        self.private = json_data.get("private", False)
        self.default = json_data.get("default", "")

        n = json_data.get("index", "")
        self._idx_set(n)

        self.types = []

    def _idx_set(self, n):
        if n == "u":
            self.idx_unique = True
        elif n in ("m", "y"):
            self.idx_multi = True
        elif n == "*":
            self.idx_array = True
        elif n == "f":
            self.idx_fulltext = True

    def __str__(self):
        dct = {
            "name": self.name,
            "type": self.type[0],
            "required": self.required,
            "descr": self.description,
            "private": self.private,
        }

        return (
            "%(name)s type: %(type)s [%(required)s] - %(descr)s - [priv: %(private)s]"
            % dct
        )

    def _get_type(self, typ):
        if not typ:
            return [FieldType.NONE, None]

        extra_typ = typ

        typ = typ.lower()
        if typ in ["str", "string", "text"]:
            return [FieldType.STR, None]
        if typ in ["int", "num", "number"]:
            return [FieldType.NUMBER, None]
        if typ in ["float", "double"]:
            return [FieldType.FLOAT, None]
        if typ in ["bool", "boolean", "check", "checkbox"]:
            return [FieldType.BOOL, None]
        if typ in ["date"]:
            return [FieldType.DATE, None]
        if typ in ["file", "upload"]:
            return [FieldType.FILE, None]
        if typ in ["json", "obj"]:
            return [FieldType.NONE, None]

        return [FieldType.CUSTOM, extra_typ]


class Endpoint:
    id: str = None
    method: str = None
    path: str = None
    parameters: list[Field] = []
    permissions: list[str] = []
    sample_data = None
    return_type: str = None
    return_description: str = None
    return_name: str = None

    short_descr: str = None
    description: str = None

    def __init__(self, json_data, mod: Module):
        self.mod = mod

        self.is_valid = False
        self.parameters = []

        self.id = json_data["id"]
        self.method = json_data["method"]
        self.path = json_data["url"]
        self.description = json_data["description"]
        self.short_descr = json_data["short_descr"]
        self.is_valid = True
        self.is_array = json_data["is_array"]
        self.return_type = json_data["returnType"]
        self.return_name = json_data["returnName"]

        for par in json_data["parameters"]:
            f = Field(par, mod)
            self.parameters.append(f)

        # Set endpoint permissions
        self.permissions = []
        perms = json_data.get("permissions", {})
        if "public" in perms:
            return

        if "logged" in perms:
            self.permissions.append("logged")
            return

        for perm in perms:
            p = mod.permissions.get(perm, None)
            if p and p.name not in self.permissions:
                self.permissions.append(p.name)
                self.mod.flow.permissions[p.id] = p

    def fields(self, skip_file_fields=False):
        if not skip_file_fields:
            return [p.name for p in self.parameters]

        return [p.name for p in self.parameters if p.type[0] != FieldType.FILE]

    def __str__(self):
        return "[%s] %s [%s]" % (self.method, self.path, self.return_type)


class Permission:  # noqa
    id: str = None
    name: str = ""
    description: str = ""

    def __init__(self, json_data: dict, mod: Module):
        self.id = json_data["id"]
        self.name = json_data["name"]
        self.description = json_data["description"]

    def __str__(self):
        dct = {
            "name": self.name,
            "descr": self.description,
        }

        return "%(name)s - %(descr)s" % dct


class Type:  # noqa
    id: str = ""
    name: str = None
    coll_table: str = ""
    coll_drop: bool = False
    fields: list[Field] = []

    def __init__(self, json_data, mod: Module):
        self.id = json_data["id"]
        self.coll_table = json_data.get("db_table", "")
        self.coll_drop = json_data.get("db_clear", False)
        self.name = json_data["name"]
        self.fields = []

        for p in json_data.get("fields", []):
            f = Field(p, mod)
            self.fields.append(f)

    def dump(self, indent_size):
        indent = " " * indent_size
        print("\n%sSTRUCTURE: %s" % (indent, self.name))
        for f in self.fields:
            print("%s    %s" % (indent, f))

    def plain_fields(self):
        return [f.name for f in self.fields]


class Module:
    endpoints: dict[str, Endpoint] = {}
    types: dict[str, Type] = {}
    permissions: dict[str, Permission] = {}
    enums: dict[str, Enum] = {}
    menus: dict[str, any] = {}
    functions: dict[str, Function] = {}

    def __init__(self, json_mod: any, flow: any):
        self.flow = flow

        self.name = json_mod["name"]

        self.types = {}
        self.endpoints = {}
        self.permissions = {}
        self.enums = {}
        self.functions = {}

        # Permissions
        for perm in json_mod.get("permissions", {}).values():
            new_perm = Permission(perm, self)
            self.permissions[new_perm.id] = new_perm
            self.flow.permissions[new_perm.id] = new_perm

        # Enums
        for enum in json_mod.get("enums", {}).values():
            new_enum = Enum(enum, self)
            self.enums[new_enum.id] = new_enum
            self.flow.enums[new_enum.id] = new_enum

        # Functions
        for func in json_mod.get("functions", {}).values():
            new_func = Function(func, self)
            self.functions[new_func.id] = new_func
            self.flow.functions[new_func.id] = new_func

        # Endpoints
        endpoints = json_mod.get("endpoints", {})
        for ep in endpoints.values():
            new_ep = Endpoint(ep, self)
            self.endpoints[new_ep.id] = new_ep
            self.flow.endpoints[new_ep.id] = new_ep

        # Types
        types = json_mod.get("types", {})
        for typ in types.values():
            new_typ = Type(typ, self)
            self.types[new_typ.id] = new_typ
            self.flow.types[new_typ.id] = new_typ

        # Menus
        self.menus = json_mod.get("menus", {}).values()

    def json_enums(self, enums):
        if not enums:
            return

        for typ in enums.values():
            en = Enum(self.parser, None, None)
            en.from_json(typ)
            # self.enums [ en.name ] = en
            self.enums[en.id] = en

    def json_functions(self, functions):
        if not functions:
            return

        for typ in functions.values():
            self._parse_json_function(typ)

    def _parse_json_function(self, j_func):
        ep = Function(self.parser, None, j_func)
        self.functions[ep.name] = ep

    def json_permissions(self, permissions):
        if not permissions:
            return

        for perm in permissions.values():
            self.permissions[perm["id"]] = perm

    def json_menus(self, menus):
        if not menus:
            return

        for menu in menus.values():
            menu = json.loads(json.dumps(menu))
            perm = self.permissions[menu.get("perm")]
            link = menu["path"]

            menu.pop("id")
            menu.pop("perm")
            menu.pop("path")

            menu["perm"] = perm["name"]
            menu["link"] = link

            self.menus.append(menu)

    # Replaces camel case names with lowercase separated by underscores
    def _replace_camel_case(self, name):
        return re.sub(r"([a-z])([A-Z])", r"\1-\2", name).lower()
