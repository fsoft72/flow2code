#!/usr/bin/env python3

"""
Tests for JSON to SQL converter
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.json_to_sql import json_to_sql


def test_basic_sqlite():
	"""Test basic SQLite conversion"""
	type_def = {
		"name": "User",
		"description": "The main user table",
		"db_table": "users",
		"fields": [
			{
				"name": "id",
				"type": "str",
				"is_required": True,
				"description": "the main id field",
				"index": "u",
				"size": 64
			},
			{
				"name": "email",
				"type": "str",
				"is_required": True,
				"description": "The user email",
				"index": "u",
				"size": 50
			},
			{
				"name": "enabled",
				"type": "boolean",
				"is_required": True,
				"description": "If the user can log in or not"
			}
		]
	}

	result = json_to_sql(type_def, 'sqlite')

	# Verify table creation (lowercase plural name)
	assert 'CREATE TABLE users' in result
	assert 'id VARCHAR(64) PRIMARY KEY' in result
	assert 'email VARCHAR(50) NOT NULL' in result
	assert 'enabled INTEGER NOT NULL' in result

	# Verify automatic timestamp fields
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP' in result

	# Verify indexes
	assert 'CREATE UNIQUE INDEX idx_users_email ON users(email)' in result

	print("✓ Basic SQLite test passed")


def test_basic_mysql():
	"""Test basic MySQL conversion"""
	type_def = {
		"name": "User",
		"description": "The main user table",
		"db_table": "users",
		"fields": [
			{
				"name": "id",
				"type": "str",
				"is_required": True,
				"description": "the main id field",
				"index": "u",
				"size": 64
			},
			{
				"name": "email",
				"type": "str",
				"is_required": True,
				"description": "The user email",
				"index": "u",
				"size": 50
			},
			{
				"name": "enabled",
				"type": "boolean",
				"is_required": True,
				"description": "If the user can log in or not"
			}
		]
	}

	result = json_to_sql(type_def, 'mysql')

	# Verify table creation (lowercase plural name)
	assert 'CREATE TABLE users' in result
	assert 'id VARCHAR(64) PRIMARY KEY' in result
	assert 'email VARCHAR(50) NOT NULL' in result
	assert 'enabled BOOLEAN NOT NULL' in result

	# Verify automatic timestamp fields
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' in result

	# Verify field comments (using -- syntax)
	assert "-- id: the main id field" in result
	assert "-- email: The user email" in result

	# Verify indexes
	assert 'CREATE UNIQUE INDEX idx_users_email ON users(email)' in result

	print("✓ Basic MySQL test passed")


def test_full_user_type_sqlite():
	"""Test full user type from data/user-type.json with SQLite"""
	# Load the actual user-type.json file
	user_type_file = Path(__file__).parent.parent / 'data' / 'user-type.json'

	with open(user_type_file, 'r') as f:
		type_def = json.load(f)

	result = json_to_sql(type_def, 'sqlite')

	# Verify key elements
	assert 'CREATE TABLE users' in result
	assert 'id VARCHAR(64) PRIMARY KEY' in result
	assert 'email VARCHAR(50) NOT NULL' in result
	assert 'username VARCHAR(50) NOT NULL' in result
	assert 'perms TEXT' in result  # JSON type -> TEXT in SQLite
	assert 'tags TEXT' in result   # Array type -> TEXT in SQLite
	assert 'enabled INTEGER NOT NULL' in result
	assert 'deleted DATE' in result

	# Verify automatic timestamp fields
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP' in result

	# Verify indexes
	assert 'CREATE UNIQUE INDEX idx_users_email ON users(email)' in result
	assert 'CREATE UNIQUE INDEX idx_users_username ON users(username)' in result
	assert 'CREATE INDEX idx_users_group ON users(group)' in result
	assert 'CREATE UNIQUE INDEX idx_users_refresh_token ON users(refresh_token)' in result

	print("✓ Full user type SQLite test passed")


def test_full_user_type_mysql():
	"""Test full user type from data/user-type.json with MySQL"""
	# Load the actual user-type.json file
	user_type_file = Path(__file__).parent.parent / 'data' / 'user-type.json'

	with open(user_type_file, 'r') as f:
		type_def = json.load(f)

	result = json_to_sql(type_def, 'mysql')

	# Verify key elements
	assert 'CREATE TABLE users' in result
	assert 'id VARCHAR(64) PRIMARY KEY' in result
	assert 'email VARCHAR(50) NOT NULL' in result
	assert 'username VARCHAR(50) NOT NULL' in result
	assert 'perms JSON' in result  # JSON type -> JSON in MySQL
	assert 'tags JSON' in result   # Array type -> JSON in MySQL
	assert 'enabled BOOLEAN NOT NULL' in result
	assert 'deleted DATE' in result

	# Verify automatic timestamp fields
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' in result

	# Verify indexes
	assert 'CREATE UNIQUE INDEX idx_users_email ON users(email)' in result
	assert 'CREATE UNIQUE INDEX idx_users_username ON users(username)' in result
	assert 'CREATE INDEX idx_users_group ON users(group)' in result

	print("✓ Full user type MySQL test passed")


def test_timestamps():
	"""Test timestamp fields with default values"""
	type_def = {
		"name": "Post",
		"fields": [
			{
				"name": "id",
				"type": "str",
				"is_required": True,
				"index": "u",
				"size": 64
			},
			{
				"name": "created",
				"type": "datetime",
				"is_required": False
			},
			{
				"name": "updated",
				"type": "datetime",
				"is_required": False
			}
		]
	}

	# SQLite
	result = json_to_sql(type_def, 'sqlite')
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP' in result

	# MySQL
	result = json_to_sql(type_def, 'mysql')
	assert 'created DATETIME DEFAULT CURRENT_TIMESTAMP' in result
	assert 'updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' in result

	print("✓ Timestamp test passed")


def test_array_fields():
	"""Test array field handling"""
	type_def = {
		"name": "Article",
		"fields": [
			{
				"name": "id",
				"type": "str",
				"is_required": True,
				"index": "u",
				"size": 64
			},
			{
				"name": "tags",
				"type": "str",
				"is_array": True
			},
			{
				"name": "metadata",
				"type": "json",
				"is_array": False
			}
		]
	}

	# SQLite
	result = json_to_sql(type_def, 'sqlite')
	assert 'tags TEXT' in result
	assert 'metadata TEXT' in result

	# MySQL
	result = json_to_sql(type_def, 'mysql')
	assert 'tags JSON' in result  # Arrays -> JSON
	assert 'metadata JSON' in result

	print("✓ Array fields test passed")


def test_invalid_dialect():
	"""Test error handling for invalid dialect"""
	type_def = {
		"name": "Test",
		"fields": [
			{"name": "id", "type": "str", "is_required": True}
		]
	}

	try:
		json_to_sql(type_def, 'postgres')
		assert False, "Should have raised ValueError"
	except ValueError as e:
		assert 'Unsupported SQL dialect' in str(e)
		print("✓ Invalid dialect test passed")


def run_all_tests():
	"""Run all tests"""
	print("\nRunning JSON to SQL converter tests...\n")

	test_basic_sqlite()
	test_basic_mysql()
	test_full_user_type_sqlite()
	test_full_user_type_mysql()
	test_timestamps()
	test_array_fields()
	test_invalid_dialect()

	print("\n✅ All tests passed!\n")


if __name__ == '__main__':
	run_all_tests()
