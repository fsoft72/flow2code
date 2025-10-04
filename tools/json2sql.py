#!/usr/bin/env python3

"""
JSON to SQL Schema Converter Tool

Converts a LiWE Flow JSON type definition to SQL table schema.
Reads from a JSON file and outputs the SQL schema to stdout.
Supports multiple SQL dialects: SQLite, MySQL, and MariaDB.

Usage:
    ./json_to_sql.py <json_file> [--dialect <dialect>]
    python3 json_to_sql.py <json_file> [--dialect <dialect>]

Example:
    ./json_to_sql.py ../data/user-type.json
    python3 json_to_sql.py ../data/user-type.json --dialect mysql > user-schema.sql
    python3 json_to_sql.py ../data/user-type.json --dialect sqlite > user-schema.sql
"""

import argparse
import json
import os
import sys

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.json_to_sql import json_to_sql


def main():
	"""Main entry point for the tool"""
	parser = argparse.ArgumentParser(
		description='Convert LiWE Flow JSON type definition to SQL table schema',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Supported SQL dialects:
  sqlite    - SQLite (default)
  mysql     - MySQL
  mariadb   - MariaDB

Examples:
  %(prog)s user-type.json
  %(prog)s user-type.json --dialect mysql > user-schema.sql
  %(prog)s ../data/user-type.json --dialect sqlite > user-schema.sql
		"""
	)
	parser.add_argument(
		'json_file',
		help='Path to the JSON file containing the type definition'
	)
	parser.add_argument(
		'-d', '--dialect',
		choices=['sqlite', 'mysql', 'mariadb'],
		default='sqlite',
		help='SQL dialect to use (default: sqlite)'
	)

	args = parser.parse_args()

	# Check if file exists
	if not os.path.isfile(args.json_file):
		print(f"Error: File not found: {args.json_file}", file=sys.stderr)
		sys.exit(1)

	# Read and parse JSON file
	try:
		with open(args.json_file, 'r') as f:
			type_def = json.load(f)
	except json.JSONDecodeError as e:
		print(f"Error: Invalid JSON in {args.json_file}: {e}", file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"Error reading file {args.json_file}: {e}", file=sys.stderr)
		sys.exit(1)

	# Convert to SQL schema
	try:
		schema = json_to_sql(type_def, args.dialect)
		print(schema)
	except Exception as e:
		print(f"Error converting to SQL schema: {e}", file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	main()
