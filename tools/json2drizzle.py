#!/usr/bin/env python3

"""
JSON to Drizzle Schema Converter Tool

Converts a LiWE Flow JSON type definition to a Drizzle ORM schema.
Reads from a JSON file and outputs the Drizzle schema to stdout.

Usage:
    ./json2drizzle.py <json_file>
    python3 json2drizzle.py <json_file>

Example:
    ./json2drizzle.py ../data/user-type.json
    python3 json2drizzle.py ../data/user-type.json > user-schema.ts
"""

import argparse
import json
import os
import sys

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.json_to_drizzle import json_to_drizzle


def main():
    """Main entry point for the tool"""
    parser = argparse.ArgumentParser(
        description='Convert LiWE Flow JSON type definition to Drizzle ORM schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s user-type.json
  %(prog)s user-type.json > user-schema.ts
  %(prog)s ../data/user-type.json
        """
    )
    parser.add_argument(
        'json_file',
        help='Path to the JSON file containing the type definition'
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

    # Convert to Drizzle schema
    try:
        schema = json_to_drizzle(type_def)
        print(schema)
    except Exception as e:
        print(f"Error converting to Drizzle schema: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
