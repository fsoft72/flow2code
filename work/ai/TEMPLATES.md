# flow2code Template Development Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Template Class Structure](#template-class-structure)
4. [TemplateBase API Reference](#templatebase-api-reference)
5. [Data Model Reference](#data-model-reference)
6. [Code Preservation System](#code-preservation-system)
7. [Text Templates System](#text-templates-system)
8. [Creating a New Template: Step-by-Step](#creating-a-new-template-step-by-step)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)

---

## Architecture Overview

flow2code uses a **template-based architecture** to generate framework-specific code from JSON flow definitions. The system is built around:

- **Data Model Layer** (`lib/types.py`): Parses flow JSON into Python objects (Module, Endpoint, Type, Field, etc.)
- **Template Base Class** (`lib/template_base.py`): Provides common functionality for all templates
- **Template Implementations** (`templates/{template_name}/`): Framework-specific code generators
- **Text Templates** (`texts.py`): String templates for code generation with placeholder substitution

### Code Generation Flow

```
Flow JSON → Module Objects → Template.code() → gen_*.py files → Output Code
```

1. `flow2code.py` parses the JSON flow file into `Module` objects
2. The specified template is dynamically loaded from `templates/{template_name}/template.py`
3. The template's `code()` method orchestrates generation of multiple output files
4. Each `gen_*.py` file generates a specific output file (types, endpoints, methods, etc.)
5. Existing files are read to extract custom code snippets (f2c_start/f2c_end blocks)
6. New code is written with snippets re-inserted

---

## Directory Structure

### Minimal Template Structure

```
templates/
└── my-template/
    ├── __init__.py          # Empty file (Python package marker)
    ├── template.py          # Main Template class
    ├── texts.py             # Text templates dictionary
    ├── gen_types.py         # Type/Enum/Interface generation
    ├── gen_endpoints.py     # Endpoint routing generation (backend only)
    ├── gen_methods.py       # Method implementation stubs (backend only)
    └── gen_actions.py       # API client actions (frontend only)
```

### Template File Responsibilities

| File | Purpose | Typical Output |
|------|---------|----------------|
| `template.py` | Main orchestrator class, extends TemplateBase | N/A (orchestration only) |
| `texts.py` | String templates with `%(placeholder)s` syntax | N/A (templates only) |
| `gen_types.py` | Generate type definitions, enums, interfaces | `types.ts`, `types.dart` |
| `gen_endpoints.py` | Generate endpoint routing (backend) | `endpoints.ts`, `index.ts` |
| `gen_methods.py` | Generate method implementation stubs (backend) | `methods.ts`, `handlers.py` |
| `gen_actions.py` | Generate API client actions (frontend) | `actions.ts`, `api.ts` |
| `gen_perms.py` | Generate permission definitions | `permissions.ts` |

---

## Template Class Structure

### Main Template Class (`template.py`)

Every template must define a `Template` class that extends `TemplateBase`:

```python
#!/usr/bin/env python3

from lib.template_base import TemplateBase
from lib.types import Module

# Import generator functions from gen_*.py files
from gen_types import generate_file_types, _gen_type
from gen_endpoints import generate_file_endpoints
from gen_methods import generate_file_methods

class Template(TemplateBase):
    def __init__(self):
        super().__init__()
        self.name = "my-template"  # Template display name

    def code(self, mod: Module, flow: any, output: str):
        """
        Main entry point called by flow2code for each module.

        @param mod: Module object with endpoints, types, enums, etc.
        @param flow: Flow2Code instance with all modules and global data
        @param output: Output directory path
        """
        # ALWAYS call parent first to initialize mod and flow
        super().code(mod, flow, output)

        # Call generator functions for each output file
        self.generate_file_types(mod, output)
        self.generate_file_endpoints(mod, output)
        self.generate_file_methods(mod, output)

# Attach generator functions as class methods
Template.generate_file_types = generate_file_types
Template._gen_type = _gen_type

Template.generate_file_endpoints = generate_file_endpoints

Template.generate_file_methods = generate_file_methods
```

### Key Points

- **Always extend `TemplateBase`**: Inherit all helper methods
- **Call `super().code()` first**: Initializes `self.mod` and `self.flow`
- **Attach generators as methods**: Use the pattern `Template.method = function` to attach functions from gen_*.py files
- **Private methods use `_` prefix**: Convention for internal helper methods

---

## TemplateBase API Reference

The `TemplateBase` class (`lib/template_base.py`) provides essential methods for all templates:

### File Management

#### `create_file(full_path: str, mod: Module, keep_all_snippets: bool = False) -> file`

Creates a new output file with automatic snippet extraction.

```python
outfile = os.path.join(output, "server", "modules", mod_name, "types.ts")
fout = self.create_file(outfile, mod)
```

**Behavior:**
- Creates all missing parent directories
- Extracts f2c_start/f2c_end blocks from existing file if present
- Returns file handle for writing
- Sets `self.snippets` dictionary with extracted code blocks

**Parameters:**
- `full_path`: Absolute path to output file
- `mod`: Module object (used for snippet name generation)
- `keep_all_snippets`: If True, preserve snippets across multiple file creations

#### `extract_snippets(mod: Module, fname: str)`

Extracts custom code blocks from existing files. Called automatically by `create_file()`.

```python
self.extract_snippets(mod, existing_file_path)
# Now self.snippets contains all extracted blocks
```

**Extracts blocks marked with:**
```typescript
/* f2c_start block_name */
  ... custom code ...
/* f2c_end block_name */
```

**Special snippets automatically created:**
- `__name_camel`: Module name as-is (e.g., "UserManagement")
- `__name_lower`: Module name in snake_case (e.g., "user_management")
- `__name_upper`: Module name in UPPER_SNAKE_CASE (e.g., "USER_MANAGEMENT")

### Naming Utilities

#### `mod_name(mod: Module) -> str`

Converts module name to snake_case for file paths and identifiers.

```python
mod_name = self.mod_name(mod)  # "User Management" → "user_management"
outfile = os.path.join(output, "modules", mod_name, "types.ts")
```

#### `valid_function_name(name: str) -> str`

Sanitizes strings to valid function/identifier names.

```python
name = self.valid_function_name("/api/user/:id")
# Result: "api_user_id"
```

**Transformations:**
- Removes path parameters (`:id` → `id`)
- Replaces `/` and `-` with `_`
- Removes all non-alphanumeric characters except `_`
- Removes duplicate underscores
- Strips leading/trailing underscores

#### `endpoint_mk_function(ep: Endpoint) -> str`

Generates function name from endpoint method + path.

```python
name = self.endpoint_mk_function(ep)
# GET /api/user/:id → "get_api_user_id"
# POST /api/auth/login → "post_api_auth_login"
```

### Field Preparation

#### `prepare_field(field: Field, template: str, template_obj: str, honour_float=False, use_enums=False, is_zod=False) -> str`

**THE MOST IMPORTANT METHOD** - Converts Field objects to language-specific type strings.

```python
# TypeScript interface field
field_str = self.prepare_field(
    field,
    TEMPL["INTERFACE_PARAM"],    # Template for normal types
    TEMPL["INTERFACE_PARAM_OBJ"], # Template for enums/objects (if use_enums=True)
    honour_float=False,            # True = "float", False = "number"
    use_enums=True,                # Use enum objects vs. strings
    is_zod=True                    # Generate Zod schema vs. TypeScript
)
```

**Returns formatted string like:**
```typescript
// With template "%(name)s: %(type)s%(opt)s"
name: string?
age: number
role: UserRole
tags: string[]
```

**Template Placeholders:**

The returned dictionary contains these placeholders for use in templates:

| Placeholder | Description | Example Values |
|-------------|-------------|----------------|
| `%(name)s` | Field name | `"email"`, `"age"` |
| `%(type)s` | Field type in target language | `"string"`, `"number"`, `"UserRole"`, `"string[]"` |
| `%(opt)s` | Optional marker | `"?"` (TypeScript), `".optional()"` (Zod), `""` (required) |
| `%(required)s` | Boolean required flag | `true`, `false` |
| `%(private)s` | Boolean private flag | `"true"`, `"false"` |
| `%(description)s` | Field description | `"User email address"` |
| `%(default)s` | Default value | `"hello"`, `42`, `""` |
| `%(param_default)s` | Default value with `=` prefix | `" = 42"`, `""` |
| `%(is_array)s` | Boolean array flag | `true`, `false` |
| `%(_req)s` | Required as string | `"true"`, `"false"` |
| `%(_is_req)s` | Required label | `"req"`, `"opt"` |
| `%(_req_param)s` | Zod/validation suffix | `""`, `".optional()"`, `", required: true"` |
| `%(_min)s` | Zod min constraint | `".min(5)"`, `""` |
| `%(_max)s` | Zod max constraint | `".max(100)"`, `""` |
| `%(type_obj)s` | Is custom type/enum | `true`, `false` |

**Type Conversion Examples:**

| Flow Type | `honour_float=False` | `honour_float=True` | `is_zod=True` | As Array |
|-----------|---------------------|---------------------|---------------|----------|
| `str` | `string` | `string` | `string()` | `string[]` / `array(z.string())` |
| `number` | `number` | `number` | `number()` | `number[]` / `array(z.number())` |
| `float` | `number` | `float` | `number()` | `number[]` / `array(z.number())` |
| `boolean` | `boolean` | `boolean` | `boolean()` | `boolean[]` |
| `date` | `Date` | `Date` | `date()` | `Date[]` |
| `datetime` | `Date` | `Date` | `string().datetime()` | `Date[]` |
| `file` | `File` | `File` | `any()` | `File[]` |
| `UserRole` (enum) | `UserRole` | `UserRole` | `ZUserRole` | `UserRole[]` |
| `User` (type) | `User` | `User` | `ZUser` | `User[]` |

**Special Type Handling:**

```python
# Custom types reference other Types/Enums
field.type = [FieldType.CUSTOM, "UserRole"]  # References enum
field.type = [FieldType.CUSTOM, "User"]      # References type

# Special LiWE types get normalized
"iliwe" → "ILiWE"
"ilrequest" → "ILRequest"
"ilresponse" → "ILResponse"

# Unknown types with strict mode
if typ.startswith(("type.", "enum.")) and flow.strict:
    raise Exception("Type or enum not found: %s" % typ)
```

### Documentation Generation

#### `mk_documentation(main_doc: str, params_doc: list[str], ret_name: str, ret_type: str, ret_doc: str, TEMPL: dict) -> str`

Generates JSDoc/PyDoc style documentation from descriptions and parameters.

```python
doc = self.mk_documentation(
    endpoint.description,         # Main description
    ["@param email - User email [req]", "@param password - Password [req]"],
    endpoint.return_name,          # "user"
    endpoint.return_type,          # "User"
    "The authenticated user",      # Return description
    TEMPL                          # Template dict with EP_DOC_RETURN
)
```

**Returns formatted JSDoc:**
```typescript
/**
 * Authenticates user with email and password
 *
 * @param email - User email [req]
 * @param password - Password [req]
 *
 * @return user: User - The authenticated user
 */
```

#### `params_and_doc(fn: Endpoint | Function, TEMPL: dict, honour_float=True) -> tuple[str, str]`

Convenience method that generates both parameter list and documentation.

```python
params_str, documentation = self.params_and_doc(endpoint, TEMPL)

# params_str = "email: string, password: string, "
# documentation = "/**\n * ...\n */"
```

**Returns:**
- `params_str`: Comma-separated parameter string with trailing `, ` (empty string if no params)
- `documentation`: Formatted JSDoc string

**Behavior:**
- Skips `FieldType.FILE` parameters
- Uses `EP_TYPED_PARAM` template from TEMPL dict
- Uses `EP_DOC_FIELD` and `EP_DOC_RETURN` templates

### Utility Methods

#### `join_newlines(lst: list[str], num_elems: int = 5) -> str`

Joins a list of strings with commas and newlines every N elements.

```python
methods = ["get_user", "create_user", "delete_user", "update_user",
           "list_users", "search_users"]
result = self.join_newlines(methods, 3)
# Result:
# get_user, create_user, delete_user,
# 	update_user, list_users, search_users
```

---

## Data Model Reference

All data model classes are defined in `lib/types.py` and represent parsed flow JSON.

### Module

**Top-level container for a flow module.**

```python
class Module:
    name: str                               # Module name (e.g., "User Management")
    endpoints: dict[str, Endpoint]          # ID → Endpoint
    types: dict[str, Type]                  # ID → Type
    enums: dict[str, Enum]                  # ID → Enum
    permissions: dict[str, Permission]      # ID → Permission
    functions: dict[str, Function]          # ID → Function
    events: dict[str, Event]                # ID → Event
    flow: Flow2Code                         # Reference to parent Flow2Code instance
```

**Usage:**
```python
for endpoint in mod.endpoints.values():
    print(endpoint.path, endpoint.method)

for typ in mod.types.values():
    print(typ.name, typ.fields)
```

### Endpoint

**API endpoint definition with method, path, parameters, and permissions.**

```python
class Endpoint:
    id: str                      # Unique identifier
    method: str                  # HTTP method: "GET", "POST", "PUT", "DELETE"
    path: str                    # URL path (e.g., "/api/user/:id")
    description: str             # Full description
    short_descr: str             # Short description
    parameters: list[Field]      # Endpoint parameters
    permissions: list[str]       # Required permission names
    return_type: str             # Return type name
    return_name: str             # Return value name
    is_array: bool               # True if returns array
    mod: Module                  # Parent module reference
```

**Methods:**

```python
# Get parameter names (optionally skip file fields)
names = endpoint.fields(skip_file_fields=True)

# Get parameters and queries separately
params, queries = endpoint.fields_ext(skip_file_fields=True)
# params: list of non-query field names
# queries: list of query field names (query=True)
```

**Permission Handling:**

```json
{
  "permissions": {
    "public": true        // No authentication required
  }
}
```

```json
{
  "permissions": {
    "logged": true        // Any authenticated user
  }
}
```

```json
{
  "permissions": {
    "user_edit": true,    // Requires "user_edit" permission
    "user_delete": true   // Requires "user_delete" permission
  }
}
```

### Type

**Data structure/schema definition (e.g., database model, interface).**

```python
class Type:
    id: str                  # Unique identifier
    name: str                # Type name (e.g., "User", "Product")
    fields: list[Field]      # Type fields
    coll_table: str          # Database collection/table name (optional)
    coll_drop: bool          # Whether to drop/recreate on deployment
```

**Methods:**

```python
# Get field names only
field_names = typ.plain_fields()  # ["name", "email", "age"]
```

**Database Metadata:**

```json
{
  "id": "user",
  "name": "User",
  "db_table": "users",
  "db_clear": false,
  "fields": [...]
}
```

### Field

**Individual field in a Type, Endpoint parameter, or Function parameter.**

```python
class Field:
    id: str                  # Field identifier
    name: str                # Field name
    type: tuple              # (FieldType enum, custom_type_name or None)
    description: str         # Field description
    default: any             # Default value
    required: bool           # Is required?
    private: bool            # Is private? (not exposed in API)
    is_array: bool           # Is array type?
    query: bool              # Is query parameter? (for endpoints)
    min_length: int          # Min length validation
    size: int                # Max size validation
    min: int                 # Min value validation
    max: int                 # Max value validation

    # Database index flags
    idx_unique: bool         # Unique index
    idx_multi: bool          # Multi-field index
    idx_array: bool          # Array index
    idx_fulltext: bool       # Fulltext index
```

**Type Tuple Structure:**

```python
field.type = (FieldType.STR, None)          # String
field.type = (FieldType.NUMBER, None)        # Number
field.type = (FieldType.CUSTOM, "UserRole")  # Custom enum
field.type = (FieldType.CUSTOM, "User")      # Custom type
```

**Index Values (from flow JSON):**

| Index Value | Flag | Meaning |
|-------------|------|---------|
| `"u"` | `idx_unique=True` | Unique index |
| `"m"` or `"y"` | `idx_multi=True` | Multi-field index |
| `"*"` | `idx_array=True` | Array index |
| `"f"` | `idx_fulltext=True` | Fulltext search index |

### Enum

**Enumeration definition with named constants.**

```python
class Enum:
    id: str                      # Unique identifier
    name: str                    # Enum name
    description: str             # Enum description
    consts: dict[str, dict]      # Constant definitions
```

**Constants Structure:**

```python
enum.consts = {
    "ADMIN": {
        "name": "admin",           # Value
        "description": "Administrator role"
    },
    "USER": {
        "name": "user",
        "description": "Regular user"
    }
}
```

### Function

**Standalone function definition (not tied to an endpoint).**

```python
class Function:
    id: str                      # Unique identifier
    name: str                    # Function name
    description: str             # Function description
    parameters: list[Field]      # Function parameters
    return_type: str             # Return type
    return_name: str             # Return value name
    is_array: bool               # True if returns array
```

**Methods:**

```python
# Get parameter names
param_names = function.fields()  # ["user_id", "email"]
```

### Permission

**Permission/authorization definition.**

```python
class Permission:
    id: str                  # Unique identifier
    name: str                # Permission name
    description: str         # Permission description
```

### FieldType Enum

**Available field types (from `lib/const.py`):**

```python
class FieldType(Enum):
    NONE = "none"
    STR = "str"
    NUMBER = "num"
    FLOAT = "float"
    BOOL = "bool"
    OBJECT = "obj"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    MULTI = "multi"      # Multiple types (union)
    FILE = "file"
    CUSTOM = "custom"    # References Type or Enum
```

---

## Code Preservation System

flow2code uses **snippet markers** to preserve custom code between regenerations.

### How It Works

1. **First Generation**: Template writes markers with empty content
2. **Developer Adds Code**: Developer writes custom code between markers
3. **Regeneration**: Template extracts existing code, regenerates file, re-inserts code

### Marker Syntax

```typescript
/* f2c_start block_name */
  ... custom code preserved here ...
/* f2c_end block_name */
```

**Language-specific comment styles:**

```typescript
// TypeScript/JavaScript
/* f2c_start block_name */
/* f2c_end block_name */
```

```python
# Python
# f2c_start block_name
# f2c_end block_name
```

```dart
// Dart
/* f2c_start block_name */
/* f2c_end block_name */
```

### Using Snippets in Templates

**Step 1: Extract snippets when creating file**

```python
fout = self.create_file(outfile, mod)
# Now self.snippets contains extracted blocks
```

**Step 2: Define placeholder in text template**

```python
texts = {
    "FUNCTION_START": """
export const %(function_name)s = async () => {
    /*=== f2c_start %(function_name)s ===*/
%(__snippet)s
    /*=== f2c_end %(function_name)s ===*/
};
"""
}
```

**Step 3: Populate and write**

```python
dct = {
    "function_name": "get_user",
    "__snippet": self.snippets["get_user"]  # Extracted or defaults to ""
}

fout.write(TEMPL["FUNCTION_START"] % dct)
```

### Common Snippet Names

| Snippet Name | Purpose | Typical Location |
|--------------|---------|------------------|
| `__file` | Custom file-level code | Top of file after imports |
| `__header` | Custom header code | After imports, before main code |
| `__file_header` | Custom file header | Very top of file |
| `{endpoint_name}` | Custom endpoint implementation | Inside endpoint function |
| `{function_name}` | Custom function implementation | Inside function |

### Best Practices

1. **Use descriptive block names**: `user_validation` not `block1`
2. **One snippet per function/method**: Easier to track
3. **Use `defaultdict`**: Template automatically converts snippets to defaultdict
   ```python
   from collections import defaultdict
   self.snippets = defaultdict(lambda: "", self.snippets)
   # Now self.snippets["missing_key"] returns "" instead of KeyError
   ```
4. **Include markers in output**: Always write both f2c_start and f2c_end markers
5. **Indent snippets properly**: Use `%(__snippet)s` with proper indentation in template

---

## Text Templates System

Text templates are Python string dictionaries with `%(placeholder)s` substitution.

### texts.py Structure

```python
#!/usr/bin/env python3

texts = {
    "FILE_START": """/* Header comment */
import { Type1, Type2 } from './types';

%(__custom_imports)s

const MODULE_NAME = "%(__name_lower)s";
""",

    "FUNCTION": """
/**
 * %(description)s
 */
export const %(name)s = (%(params)s): %(return_type)s => {
    /*=== f2c_start %(name)s ===*/
%(__snippet)s
    /*=== f2c_end %(name)s ===*/
};
""",

    "FILE_END": """
export { MODULE_NAME };
"""
}
```

### Placeholder Convention

| Prefix | Meaning | Example |
|--------|---------|---------|
| `__` (double underscore) | Template-level placeholder, usually from snippets | `%(__header)s`, `%(__snippet)s` |
| Single name | Data-level placeholder, from dct/data | `%(name)s`, `%(type)s`, `%(description)s` |

### Using Text Templates

```python
from texts import texts as TEMPL

# In generator function
dct = {
    "name": "get_user",
    "description": "Fetches user by ID",
    "params": "id: string",
    "return_type": "User",
    "__snippet": self.snippets["get_user"]
}

fout.write(TEMPL["FUNCTION"] % dct)
```

### Multi-line Templates

For readability, use triple-quoted strings:

```python
texts = {
    "COMPLEX_TEMPLATE": """
Line 1: %(var1)s
    Indented line 2: %(var2)s
    Indented line 3: %(var3)s
Line 4
""",
}
```

### Conditional Content

Use empty strings for conditional parts:

```python
dct = {
    "name": "my_func",
    "async_keyword": "async " if is_async else "",
    "await_keyword": "await " if is_async else "",
}

texts = {
    "FUNCTION": "export const %(async_keyword)sfunction %(name)s() { %(await_keyword)scall(); }"
}
```

---

## Creating a New Template: Step-by-Step

This section walks through creating a complete template from scratch.

### Step 1: Create Template Directory

```bash
cd templates
mkdir my-framework
cd my-framework
touch __init__.py
```

### Step 2: Create texts.py

Define all string templates for your generated code:

```python
#!/usr/bin/env python3

texts = {
    # Types file templates
    "TYPES_FILE_START": """// Generated by flow2code
export namespace Types {
/*=== f2c_start __file ===*/
%(__file)s
/*=== f2c_end __file ===*/
""",

    "TYPES_FILE_END": """}
""",

    "ENUM_START": """export enum %(name)s {
""",

    "ENUM_ROW": """    %(name)s = "%(value)s",
""",

    "ENUM_END": """}
""",

    "INTERFACE_START": """export interface %(name)s {
""",

    "INTERFACE_PARAM": """    %(name)s%(opt)s: %(type)s;
""",

    "INTERFACE_END": """}
""",

    # Endpoints file templates
    "ENDPOINTS_FILE_START": """// Generated by flow2code
import { Router } from './router';
import { %(methods_list)s } from './methods';

export const init = (router: Router) => {
""",

    "ENDPOINT": """    router.%(method)s("%(path)s", %(handler_name)s);
""",

    "ENDPOINTS_FILE_END": """};
""",

    # Methods file templates
    "METHODS_FILE_START": """// Generated by flow2code
import { Request, Response } from './types';

/*=== f2c_start __file_header ===*/
%(__file_header)s
/*=== f2c_end __file_header ===*/
""",

    "METHOD": """
/**
%(description)s
 */
export const %(name)s = async (%(params)s): Promise<%(return_type)s> => {
    /*=== f2c_start %(name)s ===*/
%(__snippet)s
    /*=== f2c_end %(name)s ===*/
};
""",
}
```

### Step 3: Create gen_types.py

Generate type/interface definitions:

```python
#!/usr/bin/env python3

import os
from lib.types import Module, Type, Enum
from texts import texts as TEMPL

def generate_file_types(self, mod: Module, output: str):
    """Generate types file with interfaces and enums."""
    mod_name = self.mod_name(mod)

    # Create output file path
    outfile = os.path.join(output, "src", mod_name, "types.ts")
    fout = self.create_file(outfile, mod)

    # Write file header
    fout.write(TEMPL["TYPES_FILE_START"] % self.snippets)

    # Generate enums
    for enum in mod.enums.values():
        _gen_enum(fout, enum)

    # Generate interfaces
    for typ in mod.types.values():
        self._gen_type(fout, typ)

    # Write file footer
    fout.write(TEMPL["TYPES_FILE_END"] % self.snippets)
    fout.close()

    print("Generated", outfile)


def _gen_enum(fout, enum: Enum):
    """Generate a single enum definition."""
    dct = {"name": enum.name}

    fout.write(TEMPL["ENUM_START"] % dct)

    for const_name, const_data in enum.consts.items():
        row = {
            "name": const_name,
            "value": const_data["name"]
        }
        fout.write(TEMPL["ENUM_ROW"] % row)

    fout.write(TEMPL["ENUM_END"] % dct)


def _gen_type(self, fout, typ: Type):
    """Generate a single interface/type definition."""
    dct = {"name": typ.name}

    fout.write(TEMPL["INTERFACE_START"] % dct)

    for field in typ.fields:
        field_str = self.prepare_field(
            field,
            TEMPL["INTERFACE_PARAM"],
            TEMPL["INTERFACE_PARAM"],  # Could be different for enums
            honour_float=False,
            use_enums=False,
            is_zod=False
        )
        fout.write(field_str)

    fout.write(TEMPL["INTERFACE_END"] % dct)
```

### Step 4: Create gen_endpoints.py (Backend Only)

Generate endpoint routing:

```python
#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from texts import texts as TEMPL

def generate_file_endpoints(self, mod: Module, output: str):
    """Generate endpoints routing file."""
    mod_name = self.mod_name(mod)

    outfile = os.path.join(output, "src", mod_name, "endpoints.ts")
    fout = self.create_file(outfile, mod)

    # Collect method names for import
    method_names = []
    for ep in mod.endpoints.values():
        method_names.append(self.endpoint_mk_function(ep))

    self.snippets["methods_list"] = ", ".join(method_names)

    # Write header
    fout.write(TEMPL["ENDPOINTS_FILE_START"] % self.snippets)

    # Write endpoint registrations
    for ep in mod.endpoints.values():
        handler_name = self.endpoint_mk_function(ep)
        dct = {
            "method": ep.method.lower(),
            "path": ep.path,
            "handler_name": handler_name
        }
        fout.write(TEMPL["ENDPOINT"] % dct)

    # Write footer
    fout.write(TEMPL["ENDPOINTS_FILE_END"] % self.snippets)
    fout.close()

    print("Generated", outfile)
```

### Step 5: Create gen_methods.py (Backend) or gen_actions.py (Frontend)

**Backend - Method implementations:**

```python
#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from lib.utils import type2typescript
from texts import texts as TEMPL

def generate_file_methods(self, mod: Module, output: str):
    """Generate method implementation stubs."""
    mod_name = self.mod_name(mod)

    outfile = os.path.join(output, "src", mod_name, "methods.ts")
    fout = self.create_file(outfile, mod)

    # Write header
    fout.write(TEMPL["METHODS_FILE_START"] % self.snippets)

    # Generate each endpoint method
    for ep in mod.endpoints.values():
        _gen_method(self, fout, ep)

    fout.close()
    print("Generated", outfile)


def _gen_method(self, fout, ep: Endpoint):
    """Generate a single method implementation."""
    method_name = self.endpoint_mk_function(ep)

    # Build parameters string and documentation
    params_str, documentation = self.params_and_doc(ep, TEMPL)

    # Determine return type
    return_type = type2typescript(ep.return_type, self.mod.flow)
    if ep.is_array:
        return_type += "[]"

    dct = {
        "name": method_name,
        "description": documentation,
        "params": params_str,
        "return_type": return_type,
        "__snippet": self.snippets[method_name]
    }

    fout.write(TEMPL["METHOD"] % dct)
```

**Frontend - API actions:**

```python
#!/usr/bin/env python3

import os
from lib.types import Module, Endpoint
from texts import texts as TEMPL

def generate_file_actions(self, mod: Module, output: str):
    """Generate API client actions."""
    mod_name = self.mod_name(mod)

    outfile = os.path.join(output, "src", mod_name, "actions.ts")
    fout = self.create_file(outfile, mod)

    # Write header
    fout.write(TEMPL["ACTIONS_FILE_START"] % self.snippets)

    # Generate each action
    for ep in mod.endpoints.values():
        _gen_action(self, fout, ep)

    fout.close()
    print("Generated", outfile)


def _gen_action(self, fout, ep: Endpoint):
    """Generate a single API action."""
    action_name = self.endpoint_action_name(ep)

    # Get field names for request body
    fields = ep.fields(skip_file_fields=True)

    # Get query parameters
    params, queries = ep.fields_ext(skip_file_fields=True)

    dct = {
        "action_name": action_name,
        "method": ep.method.lower(),
        "path": ep.path,
        "fields": ", ".join(fields),
        "has_body": "true" if fields else "false",
        "__snippet": self.snippets[action_name]
    }

    fout.write(TEMPL["ACTION"] % dct)
```

### Step 6: Create template.py

Main template orchestrator:

```python
#!/usr/bin/env python3

from lib.template_base import TemplateBase
from lib.types import Module, Endpoint

from gen_types import generate_file_types, _gen_type
from gen_endpoints import generate_file_endpoints
from gen_methods import generate_file_methods

class Template(TemplateBase):
    def __init__(self):
        super().__init__()
        self.name = "my-framework"

    def code(self, mod: Module, flow: any, output: str):
        """Generate all files for this module."""
        super().code(mod, flow, output)

        self.generate_file_types(mod, output)
        self.generate_file_endpoints(mod, output)
        self.generate_file_methods(mod, output)

    @staticmethod
    def endpoint_action_name(ep: Endpoint) -> str:
        """Generate action name from endpoint path (frontend)."""
        name = ep.path.replace("/", "_").lower().split(":")[0]
        name = name.replace("-", "_").strip("_")
        return name

# Attach generator functions
Template.generate_file_types = generate_file_types
Template._gen_type = _gen_type

Template.generate_file_endpoints = generate_file_endpoints

Template.generate_file_methods = generate_file_methods
```

### Step 7: Test Your Template

```bash
cd ../..  # Back to flow2code root
./flow2code.py examples/user.json -t my-framework -o /tmp/test-output
```

Check generated files in `/tmp/test-output`.

---

## Best Practices

### 1. File Organization

**DO:**
- One gen_*.py file per output file
- Keep generator functions focused and single-purpose
- Use private helper functions (prefix with `_`)

**DON'T:**
- Put all generators in template.py
- Mix concerns (types + endpoints in one file)

### 2. Snippet Management

**DO:**
```python
# Create file and extract snippets
fout = self.create_file(outfile, mod)

# Use defaultdict for missing snippets
from collections import defaultdict
self.snippets = defaultdict(lambda: "", self.snippets)

# Reference snippets in templates
dct["__snippet"] = self.snippets[function_name]
```

**DON'T:**
```python
# Access snippets without defaultdict (causes KeyError)
snippet = self.snippets[function_name]  # Will crash if missing

# Forget to extract snippets
fout = open(outfile, "w")  # Skips extraction!
```

### 3. Type Conversion

**DO:**
```python
# Use prepare_field for all field type conversions
field_str = self.prepare_field(
    field,
    TEMPL["PARAM"],
    TEMPL["PARAM_OBJ"],
    honour_float=False,
    use_enums=False,
    is_zod=False
)

# Use type2typescript for return types
return_type = type2typescript(ep.return_type, self.mod.flow)
```

**DON'T:**
```python
# Manual type conversion (fragile, incomplete)
if field.type[0] == FieldType.STR:
    typ = "string"
elif field.type[0] == FieldType.NUMBER:
    typ = "number"
# ... missing many cases
```

### 4. Module Naming

**DO:**
```python
# Use mod_name() for file paths
mod_name = self.mod_name(mod)
outfile = os.path.join(output, "modules", mod_name, "types.ts")

# Use snippets for module name variations
# __name_camel, __name_lower, __name_upper auto-generated
fout.write("const MODULE = '%(__name_upper)s';" % self.snippets)
```

**DON'T:**
```python
# Manual string manipulation (inconsistent)
mod_name = mod.name.lower().replace(" ", "_")
```

### 5. Documentation

**DO:**
```python
# Use built-in documentation generators
params_str, documentation = self.params_and_doc(endpoint, TEMPL)

# Or build manually
doc = self.mk_documentation(
    endpoint.description,
    param_docs,
    endpoint.return_name,
    endpoint.return_type,
    return_description,
    TEMPL
)
```

**DON'T:**
```python
# Build JSDoc manually (error-prone)
doc = "/**\n"
doc += " * " + endpoint.description + "\n"
for param in endpoint.parameters:
    doc += " * @param " + param.name + "\n"
# ...
```

### 6. Error Handling

**DO:**
```python
# Use strict mode to catch missing types
if self.mod.flow.strict and typ.startswith("type."):
    raise Exception(f"Type not found: {typ}")

# Validate critical data
if not mod.endpoints:
    print(f"Warning: No endpoints in module {mod.name}")
    return
```

**DON'T:**
```python
# Silently ignore missing data
typ = types.get(field.type[1], "any")  # Hides errors
```

### 7. Permissions

**DO:**
```python
# Check for special permissions first
if endpoint.permissions == []:
    # Public endpoint
    perms_check = ""
elif "logged" in endpoint.permissions:
    perms_check = "requireAuth()"
else:
    # Named permissions
    perms_check = f"requirePerms({endpoint.permissions})"
```

**DON'T:**
```python
# Assume all endpoints have permissions
perms_check = f"check({endpoint.permissions[0]})"  # May crash
```

### 8. Output Paths

**DO:**
```python
# Use os.path.join for cross-platform paths
outfile = os.path.join(output, "server", "modules", mod_name, "types.ts")

# Let create_file handle directory creation
fout = self.create_file(outfile, mod)
```

**DON'T:**
```python
# Manual path building (breaks on Windows)
outfile = f"{output}/server/modules/{mod_name}/types.ts"

# Manual directory creation
os.makedirs(os.path.dirname(outfile))  # create_file does this
```

---

## Common Patterns

### Pattern 1: Collecting Import Lists

**Problem**: Need to import generated types/methods in other files.

**Solution**:

```python
# In generate_file_endpoints.py
def generate_file_endpoints(self, mod: Module, output: str):
    # Collect all method names
    method_names = []
    for ep in mod.endpoints.values():
        method_names.append(self.endpoint_mk_function(ep))

    # Store in snippets for use in template
    self.snippets["__methods"] = ", ".join(method_names)

    # Write header with imports
    fout.write(TEMPL["HEADER"] % self.snippets)
```

```python
# In texts.py
texts = {
    "HEADER": """import {
    %(__methods)s
} from './methods';
"""
}
```

### Pattern 2: Conditional Template Selection

**Problem**: Enums need different templates than interfaces.

**Solution**:

```python
# Use template_obj parameter
field_str = self.prepare_field(
    field,
    TEMPL["PARAM"],          # Normal template
    TEMPL["PARAM_OBJ"],      # Enum/object template
    use_enums=True            # Switch to PARAM_OBJ for enums
)
```

```python
# In texts.py
texts = {
    "PARAM": "%(name)s: %(type)s%(opt)s",
    "PARAM_OBJ": "{ name: '%(name)s', type: %(type)sObj }"
}
```

### Pattern 3: Database Collection Initialization

**Problem**: Backend needs to initialize database collections.

**Solution**:

```python
def _gen_db_init(mod: Module, TEMPL: dict) -> str:
    """Generate database initialization code."""
    res = []

    for typ in mod.types.values():
        if not typ.coll_table:
            continue

        # Build index definitions
        indexes = []
        for field in typ.fields:
            if field.idx_unique:
                indexes.append(f'{{ field: "{field.name}", unique: true }}')
            elif field.idx_multi:
                indexes.append(f'{{ field: "{field.name}", unique: false }}')

        if indexes:
            dct = {
                "table": typ.coll_table,
                "indexes": ", ".join(indexes),
                "drop": "true" if typ.coll_drop else "false"
            }
            res.append(TEMPL["COLL_INIT"] % dct)

    return "\n".join(res)

# Use in function generation
def _generate_function(self, fout, fn: Function, mod: Module):
    dct = {
        "name": fn.name,
        "__pre_snippet": "",
        "__snippet": self.snippets[fn.name],
    }

    # Special handling for db_init function
    if fn.name.endswith("_db_init"):
        dct["__pre_snippet"] = _gen_db_init(mod, TEMPL)

    fout.write(TEMPL["FUNCTION"] % dct)
```

### Pattern 4: Handling File Upload Parameters

**Problem**: File upload parameters need special handling.

**Solution**:

```python
# Skip file parameters in most contexts
for param in endpoint.parameters:
    if param.type[0] == FieldType.FILE:
        continue  # Skip file uploads

    # Process other parameters
    ...

# Or use built-in helper
param_names = endpoint.fields(skip_file_fields=True)
```

### Pattern 5: Query vs. Body Parameters

**Problem**: Frontend needs to know which params go in URL vs. request body.

**Solution**:

```python
# Use fields_ext to separate
params, queries = endpoint.fields_ext(skip_file_fields=True)

# Build URL with query string
query_str = "&".join([f"{q}=${{{q}}}" for q in queries])
url = f"{endpoint.path}?{query_str}" if queries else endpoint.path

# Build request body with params
body = "{" + ", ".join(params) + "}"
```

### Pattern 6: Array Return Types

**Problem**: Endpoints can return arrays of types.

**Solution**:

```python
return_type = type2typescript(endpoint.return_type, self.mod.flow)

if endpoint.is_array:
    return_type += "[]"

dct = {"return_type": return_type}
```

### Pattern 7: Custom Helper Methods

**Problem**: Template needs framework-specific naming.

**Solution**:

```python
class Template(TemplateBase):
    def __init__(self):
        super().__init__()
        self.name = "my-framework"

    @staticmethod
    def endpoint_action_name(ep: Endpoint) -> str:
        """Custom naming for frontend actions."""
        name = ep.path.replace("/", "_").lower()
        name = name.split(":")[0]  # Remove :id params
        name = name.replace("-", "_")
        name = name.strip("_")
        return f"act_{name}"  # Prefix with "act_"

# Use in generators
action_name = self.endpoint_action_name(endpoint)
```

### Pattern 8: Folding Markers (Editor Support)

**Problem**: Generated files with many functions are hard to navigate.

**Solution**:

```python
# Add folding markers before/after functions
texts = {
    "FOLDING_START": "// {{{ %(name)s",
    "FOLDING_END": "// }}}\n\n",

    "FUNCTION": """
%(folding_start)s
export const %(name)s = () => {
    ...
};
%(folding_end)s
"""
}

# Use in generator
dct = {
    "name": "get_user",
    "folding_start": TEMPL["FOLDING_START"] % {"name": "get_user"},
    "folding_end": TEMPL["FOLDING_END"]
}
```

### Pattern 9: Module Name Variations

**Problem**: Need module name in different cases (camelCase, snake_case, UPPER_CASE).

**Solution**:

```python
# These are automatically available in self.snippets:
# __name_camel  - Original name ("User Management")
# __name_lower  - snake_case ("user_management")
# __name_upper  - UPPER_SNAKE_CASE ("USER_MANAGEMENT")

fout.write("const MODULE = '%(__name_upper)s';\n" % self.snippets)
fout.write("import %(__name_lower)s from './lib';\n" % self.snippets)
```

### Pattern 10: Zod Schema Generation

**Problem**: Need both TypeScript types and Zod schemas.

**Solution**:

```python
# Generate Zod schema
zod_field = self.prepare_field(
    field,
    "%(name)s: zodMeta(z.%(type)s%(opt)s, { priv: %(private)s }),",
    "",
    is_zod=True
)

# Generate TypeScript type from Zod
texts = {
    "TYPE_DEF": """
export const Z%(name)s = z.object({
%(fields)s
});

export type %(name)s = z.infer<typeof Z%(name)s>;
"""
}
```

---

## Appendix: Complete Example

See `templates/liwe3-nodejs-ng/` for a complete, production-ready template implementation.

**Key files to study:**

- `template.py`: Main orchestrator with helper methods
- `gen_types.py`: Zod schemas + TypeScript types
- `gen_endpoints.py`: Express route registration with permissions
- `gen_methods.py`: Method stubs with database initialization
- `texts.py`: Comprehensive text templates

---

## Summary Checklist

When creating a new template:

- [ ] Create `templates/{name}/` directory
- [ ] Add `__init__.py` (empty file)
- [ ] Create `texts.py` with all string templates
- [ ] Create `gen_types.py` for types/enums/interfaces
- [ ] Create `gen_endpoints.py` OR `gen_actions.py` (backend vs. frontend)
- [ ] Create `gen_methods.py` (backend) or additional generators
- [ ] Create `template.py` with Template class
- [ ] Extend `TemplateBase` in Template class
- [ ] Implement `code(mod, flow, output)` method
- [ ] Call `super().code()` first
- [ ] Attach all generator functions as class methods
- [ ] Use `create_file()` to handle snippets automatically
- [ ] Use `prepare_field()` for field type conversions
- [ ] Use `mod_name()` for consistent module naming
- [ ] Test with example flow files
- [ ] Verify snippet preservation on regeneration

---

## Getting Help

- **Existing templates**: Study `templates/liwe3-nodejs-ng/` and `templates/liwe3-svelte-ng/`
- **Core library**: Read `lib/template_base.py` and `lib/types.py` for API details
- **Example flows**: Test with files in `examples/` directory
- **Flow format**: See `CLAUDE.md` for flow file structure

