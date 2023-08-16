#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from texts import texts as TEMPL

# ==================================================================================================
# INTERNAL FUNCTIONS
# ==================================================================================================


# ==================================================================================================
# CLASS METHODS
# ==================================================================================================
def generate_file_actions(self, mod: Module, output: str):
    mod_name = self.mod_name(mod)

    # create the output directory
    outfile = os.path.join(output, "src", "modules", mod_name, "actions.ts")
    fout = self.create_file(outfile, mod)

    fout.write(TEMPL["ACTIONS_FILE_HEADER"] % self.snippets)

    for ep in mod.endpoints.values():
        self._gen_action(fout, ep)

    # close the output file
    fout.close()
    print("Generated", outfile)


def _gen_action(self, fout, ep: Endpoint):
    (params, doc) = self.params_and_doc(ep, TEMPL, honour_float=False)

    fields = ep.fields()
    if len(fields) > 3:
        fields.sort()
        fields = "\n\t\t" + ",\n\t\t".join(fields) + "\n\t"
    else:
        fields = ", ".join(fields)

    dct = {
        "action_name": self.endpoint_action_name(ep),  # , "act_"),
        "action_const": self.endpoint_action_name(ep).upper(),
        "method": ep.method.lower(),
        "url": ep.path,
        "fields": fields  # "\n\t\t" + ",\n\t\t".join(ep.fields()) + "\n\t"
        if ep.fields()
        else "",
        "params": params,
        "return_name": ep.return_name,
        "_needs_perms": "true" if ep.permissions else "false",
        "__doc": doc,
    }

    if dct["method"] == "delete":
        dct["method"] = "delete_"

    if dct["fields"]:
        dct["fields"] = " %(fields)s " % dct

    if ep.return_name == "__plain__":
        dct["_return_payload"] = "__data"
    else:
        dct["_return_payload"] = "__data.%(return_name)s" % dct

    if dct["params"]:
        dct["params"] += "onsuccess?: any, onerror?: any"
    else:
        dct["params"] = "onsuccess?: any, onerror?: any"

    fout.write(TEMPL["ACTION_START"] % dct)
