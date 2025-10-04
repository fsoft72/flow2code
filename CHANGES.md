# CHANGES.md

## 2025-10-04

### Added - Cloudflare Workers Template

- Created new `liwe3-cloudflare` template for generating Cloudflare Workers compatible code
  - Based on `liwe3-nodejs-ng` template architecture
  - Uses Hono framework for HTTP routing
  - Implements Zod schema validation
  - Supports Drizzle ORM for database operations
  - Generates complete module structure with tests configuration

#### Template Structure
- `templates/liwe3-cloudflare/template.py` - Main template class extending TemplateBase
- `templates/liwe3-cloudflare/texts.py` - Template strings for all generated files
- `templates/liwe3-cloudflare/gen_index.py` - Generates module index with Hono endpoints
- `templates/liwe3-cloudflare/gen_perms.py` - Generates permissions definitions
- `templates/liwe3-cloudflare/gen_methods.py` - Generates individual method files with Zod validation
- `templates/liwe3-cloudflare/gen_schema.py` - Generates Drizzle ORM table schemas
- `templates/liwe3-cloudflare/gen_sql.py` - Generates SQLite SQL schema files
- `templates/liwe3-cloudflare/gen_config.py` - Generates configuration files

#### Generated Files
- `src/index.ts` - Module initialization with Hono endpoint registration
  - Different templates for GET, POST, PUT, PATCH, DELETE methods
  - Error handling for body parsing
  - Query parameter handling for GET requests

- `src/perms.ts` - Module permissions array
  - SystemPermission type definitions
  - JSDoc documentation
  - Proper quote escaping in descriptions

- `src/methods/` - Individual method files
  - Zod schema definitions with validation
  - Type inference for parameters and results
  - Full JSDoc documentation
  - f2c preservation blocks for custom code
  - Parameter extraction and validation

- `src/methods/index.ts` - Re-exports all methods and types
- `src/methods/utils.ts` - Common imports (LiWE core, Drizzle ORM, Zod)
- `src/methods.ts` - Backward compatibility wrapper

- `src/schema.ts` - Drizzle ORM table definitions
  - Generated only for types with `coll_table` field
  - Includes indexes (unique, multi, array, fulltext)
  - JSDoc comments for tables and fields
  - Type inference exports

- `sql/{module_name}.sql` - SQLite schema file
  - Table definitions with field comments
  - Index creation statements
  - Generated only for types with `coll_table` field

- `package.json` - Module package configuration
  - Workspace dependencies
  - TypeScript and Vitest setup
  - Build and test scripts

- `tsconfig.json` - TypeScript compiler configuration
  - ES2022 target with ESNext modules
  - Bundler module resolution
  - Declaration file generation

- `vitest.config.ts` - Vitest testing framework configuration
  - Path aliases for core imports
  - Test file patterns
  - Coverage reporting

#### Key Features
- **Zod Integration**: Uses `lib/json_to_zod.py` for schema generation
  - Custom type resolution from module flow definitions
  - Array and optional field support
  - String length validation (min/max)

- **Drizzle Integration**: Uses `lib/json_to_drizzle.py` for ORM schemas
  - Field index flags converted to string format
  - Handles missing attributes gracefully
  - Type inference support

- **SQL Generation**: Uses `lib/json_to_sql.py` for schema files
  - SQLite dialect support
  - Inline field documentation
  - Index creation

- **File Naming**: Endpoint paths converted to file names
  - `/user/add` → `user-add.ts`
  - Path parts joined with dashes

- **Code Preservation**: f2c_start/f2c_end blocks for custom code retention

### Added - Core Libraries

- Created `lib/json_to_drizzle.py` module to convert LiWE Flow JSON type definitions to Drizzle ORM schemas
  - Maps flow field types to native Drizzle types (boolean, date, timestamp, text, integer, etc.)
  - Generates JSDoc comments for tables, fields, and indexes
  - Auto-pluralizes table names to lowercase
  - Supports all index types (unique, multi, array, fulltext)
  - Includes type inference exports

- Created `tools/json2drizzle.py` CLI tool to convert JSON files to Drizzle schemas
  - Reads JSON type definition from file
  - Outputs formatted Drizzle schema to stdout
  - Includes error handling and help documentation

- Added comprehensive test suite in `tests/test_json_to_drizzle.py`
  - 34 unit tests covering all functionality
  - Tests helper functions, main conversion, and edge cases
  - Uses `data/user-type.json` as test fixture

- Created `CLAUDE.md` with comprehensive project documentation for Claude Code instances
  - Core architecture overview
  - Template system documentation
  - Common commands and workflow
  - Flow file format specification
  - Key implementation details and conventions

### Changed
- Type mappings now use native Drizzle types instead of SQLite-specific conversions
  - `boolean` → `boolean()` (was `integer()`)
  - `date` → `date()` (was `text()`)
  - `datetime` → `timestamp()` (was `text()`)
  - This allows easier database switching and lets Drizzle handle type conversion

### Fixed
- Quote escaping in permission descriptions (e.g., "user's tag")
- Custom type resolution in Zod schemas now uses actual type/enum names
- Field attribute handling for `size` instead of `max_length`
- Index flag conversion from boolean attributes to string format
