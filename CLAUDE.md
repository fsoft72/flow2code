# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

flow2code is a Python-based code generator that converts LiWE Flow JSON schema definitions into production-ready code for multiple frameworks and languages. The tool reads JSON flow files containing module definitions (endpoints, types, enums, permissions, functions) and generates framework-specific code using a template-based architecture.

## Core Architecture

### Main Entry Point
- `flow2code.py` - CLI tool that orchestrates the entire code generation process
  - Parses flow JSON files (supports both single module and multi-module formats with `modules` or `mods` keys)
  - Loads template modules dynamically from `templates/{template_name}/template.py`
  - Delegates code generation to template instances

### Data Model (`lib/types.py`)
The core data structures that represent the parsed flow file:
- `Module` - Top-level container for a flow module (contains endpoints, types, enums, permissions, functions)
- `Endpoint` - API endpoint definition (method, path, parameters, permissions, return type)
- `Type` - Data structure/schema definition with fields
- `Field` - Individual field in a Type or Endpoint parameter (supports types from `lib/const.py::FieldType`)
- `Enum` - Enumeration definition with constants
- `Function` - Standalone function definition
- `Permission` - Permission/authorization definition

### Template System (`lib/template_base.py`)
`TemplateBase` is the abstract base class all templates inherit from. Key features:
- **Snippet Extraction**: Parses existing generated files for `f2c_start/f2c_end` or `d2r_start/d2r_end` blocks to preserve custom code between regenerations
- **File Management**: `create_file()` method handles directory creation and snippet extraction
- **Field Preparation**: `prepare_field()` method converts Field objects to template-ready dictionaries with type conversion (supports TypeScript, Zod schema, and framework-specific formats)
- **Helper Methods**: Module naming (`mod_name`), function naming (`valid_function_name`, `endpoint_mk_function`), documentation generation (`mk_documentation`, `params_and_doc`)

### Available Templates

#### Backend Templates (Node.js)
- `liwe3-nodejs` - Legacy Node.js backend (TypeScript)
- `liwe3-nodejs-ng` - Next-generation Node.js backend with improved structure
  - Generates: `endpoints.ts`, `methods.ts`, `types.ts`, `permissions.ts`
  - Uses Zod for schema validation

#### Frontend Templates
- `liwe3-nextjs` - Next.js/React frontend with Zod schemas
  - Generates: `types.ts`, `actions.ts` (server actions)
- `liwe3-svelte` - Legacy Svelte frontend
- `liwe3-svelte-ng` - Next-generation Svelte frontend with Svelte 5 runes
  - Generates: `types.ts`, `actions.ts`

#### Mobile Templates
- `liwe3-dart` - Flutter/Dart code generation

### Template Structure
Each template directory contains:
- `__init__.py` - Package initialization
- `template.py` - Main Template class extending TemplateBase
- `gen_*.py` - Specific file generators (e.g., `gen_types.py`, `gen_endpoints.py`, `gen_methods.py`)
- `texts.py` - Template strings dictionary (e.g., `TEMPL["TYPES_FILE_START"]`)

## Common Commands

### Basic Usage
```bash
# Generate code from a flow file
./flow2code.py examples/user.json -t liwe3-nodejs-ng -o ./output

# With strict mode (fails on missing type/enum references)
./flow2code.py examples/user.json -t liwe3-nodejs-ng -o ./output --strict

# Show version
./flow2code.py --version
```

### Development Workflow
```bash
# Test with example flow files
./flow2code.py examples/user.json -t liwe3-nodejs-ng -o /tmp/test-output
./flow2code.py examples/pet-small.json -t liwe3-svelte-ng -o /tmp/test-output
./flow2code.py examples/academy.json -t liwe3-nextjs -o /tmp/test-output
```

## Flow File Format

Flow files are JSON documents with this structure:
```json
{
  "mods": {
    "module_id": {
      "name": "ModuleName",
      "endpoints": {},
      "types": {},
      "enums": {},
      "permissions": {},
      "functions": {}
    }
  }
}
```

Or for single modules, omit the `mods` wrapper and use keys directly: `name`, `endpoints`, `types`, etc.

## Key Implementation Details

### Field Type Mapping
The `prepare_field()` method in `TemplateBase` handles conversion between flow types and target language types:
- Flow types: `str`, `number`, `float`, `boolean`, `date`, `datetime`, `file`, `json`, custom types
- Supports arrays via `is_array` flag
- Handles required/optional fields
- Supports min/max length validation (for Zod schemas)
- Custom types reference other Types/Enums in the flow

### Code Preservation
Generated files use special comment markers to preserve custom code:
- `/* f2c_start block_name */` ... `/* f2c_end block_name */`
- Or legacy: `/* d2r_start block_name */` ... `/* d2r_end block_name */`
- Snippets are extracted before file regeneration and re-inserted via `%(block_name)s` placeholders

### Endpoint Processing
- Endpoint paths can contain parameters (e.g., `/user/:id`)
- Method + path combinations generate function names via `endpoint_mk_function()`
- Parameters marked with `query: true` are treated as query parameters
- File upload parameters (`type: file`) are often skipped in certain contexts via `skip_file_fields`

## Important Conventions

### Naming Conventions
- Module names: converted to `snake_case` via `mod_name()` method
- Endpoint function names: generated from HTTP method + path, sanitized to valid identifiers
- Type/Enum names: preserved as-is from flow file (usually PascalCase)

### Permissions
- Special permission `"public": true` means no authentication required
- Special permission `"logged": true` means any authenticated user
- Named permissions reference `Permission` objects defined in the module

### Database Fields
Types can have database metadata:
- `db_table` - Collection/table name
- `db_clear` - Whether to drop/recreate on deployment
- Field `index` values: `u` (unique), `m`/`y` (multi), `*` (array), `f` (fulltext)

## Branch and Version Information

- Main branch: `master`
- Current working branch: `liwe3-ng` (next-generation templates development)
- Version: 0.3.1 (defined in `flow2code.py`)
