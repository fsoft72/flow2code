# CHANGES.md

## 2025-10-04

### Added
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
