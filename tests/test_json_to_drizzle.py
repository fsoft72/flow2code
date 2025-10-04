#!/usr/bin/env python3

"""
Unit tests for json_to_drizzle module
"""

import json
import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.json_to_drizzle import (
    json_to_drizzle,
    _get_drizzle_type,
    _format_drizzle_options,
    _pluralize_table_name,
    _get_index_description
)


class TestJsonToDrizzleHelpers(unittest.TestCase):
    """Test helper functions"""

    def test_get_drizzle_type_string(self):
        """Test string type mapping"""
        drizzle_type, options = _get_drizzle_type('str', 50, False)
        self.assertEqual(drizzle_type, 'text')
        self.assertEqual(options, {'length': 50})

    def test_get_drizzle_type_number(self):
        """Test number type mapping"""
        drizzle_type, options = _get_drizzle_type('num', 0, False)
        self.assertEqual(drizzle_type, 'integer')
        self.assertEqual(options, {})

    def test_get_drizzle_type_boolean(self):
        """Test boolean type mapping"""
        drizzle_type, options = _get_drizzle_type('boolean', 0, False)
        self.assertEqual(drizzle_type, 'boolean')
        self.assertEqual(options, {})

    def test_get_drizzle_type_json(self):
        """Test JSON type mapping"""
        drizzle_type, options = _get_drizzle_type('json', 0, False)
        self.assertEqual(drizzle_type, 'text')
        self.assertEqual(options, {'mode': 'json'})

    def test_get_drizzle_type_date(self):
        """Test date type mapping"""
        drizzle_type, options = _get_drizzle_type('date', 0, False)
        self.assertEqual(drizzle_type, 'date')
        self.assertEqual(options, {})

    def test_get_drizzle_type_datetime(self):
        """Test datetime type mapping"""
        drizzle_type, options = _get_drizzle_type('datetime', 0, False)
        self.assertEqual(drizzle_type, 'timestamp')
        self.assertEqual(options, {})

    def test_format_drizzle_options_empty(self):
        """Test formatting empty options"""
        result = _format_drizzle_options({})
        self.assertEqual(result, '')

    def test_format_drizzle_options_length(self):
        """Test formatting length option"""
        result = _format_drizzle_options({'length': 50})
        self.assertEqual(result, '{ length: 50 }')

    def test_format_drizzle_options_mode(self):
        """Test formatting mode option"""
        result = _format_drizzle_options({'mode': 'json'})
        self.assertEqual(result, "{ mode: 'json' }")

    def test_format_drizzle_options_multiple(self):
        """Test formatting multiple options"""
        result = _format_drizzle_options({'length': 100, 'mode': 'json'})
        self.assertIn('length: 100', result)
        self.assertIn("mode: 'json'", result)

    def test_pluralize_table_name_simple(self):
        """Test simple pluralization"""
        self.assertEqual(_pluralize_table_name('User'), 'users')
        self.assertEqual(_pluralize_table_name('Post'), 'posts')

    def test_pluralize_table_name_y_ending(self):
        """Test pluralization of words ending in y"""
        self.assertEqual(_pluralize_table_name('Category'), 'categories')
        self.assertEqual(_pluralize_table_name('Company'), 'companies')

    def test_pluralize_table_name_special_endings(self):
        """Test pluralization of words with special endings"""
        self.assertEqual(_pluralize_table_name('Batch'), 'batches')
        self.assertEqual(_pluralize_table_name('Box'), 'boxes')

    def test_pluralize_table_name_already_plural(self):
        """Test that already plural words are unchanged"""
        self.assertEqual(_pluralize_table_name('Users'), 'users')

    def test_get_index_description_common_fields(self):
        """Test index descriptions for common fields"""
        self.assertIn('email', _get_index_description('email', 'u'))
        self.assertIn('domain', _get_index_description('domain', 'y'))
        # Enabled has a specific description about filtering
        self.assertIn('filtering', _get_index_description('enabled', 'm'))

    def test_get_index_description_generic(self):
        """Test generic index description"""
        result = _get_index_description('custom_field', 'y')
        self.assertIn('custom_field', result)


class TestJsonToDrizzleConverter(unittest.TestCase):
    """Test main conversion function"""

    @classmethod
    def setUpClass(cls):
        """Load the user type JSON fixture"""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'user-type.json'
        )
        with open(fixture_path, 'r') as f:
            cls.user_type = json.load(f)

    def test_json_to_drizzle_output_structure(self):
        """Test that output has expected structure"""
        result = json_to_drizzle(self.user_type)

        # Check for essential elements
        self.assertIn('export const users = sqliteTable', result)
        self.assertIn('export type User = typeof users.$inferSelect', result)
        self.assertIn('/**', result)  # Has JSDoc comments
        self.assertIn('*/', result)

        # Check for automatic timestamp fields
        self.assertIn('created: timestamp( \'created\' )', result)
        self.assertIn('updated: timestamp( \'updated\' )', result)
        self.assertIn('.default( sql`CURRENT_TIMESTAMP` )', result)

    def test_json_to_drizzle_table_name(self):
        """Test that table name is correctly generated"""
        result = json_to_drizzle(self.user_type)
        self.assertIn("sqliteTable( 'users'", result)

    def test_json_to_drizzle_primary_key_field(self):
        """Test that id field is marked as primary key"""
        result = json_to_drizzle(self.user_type)
        self.assertIn('id: text( \'id\'', result)
        self.assertIn('.primaryKey()', result)
        self.assertIn('.notNull()', result)

    def test_json_to_drizzle_required_fields(self):
        """Test that required fields have .notNull()"""
        result = json_to_drizzle(self.user_type)

        # email is required
        email_idx = result.find("email: text( 'email'")
        notNull_idx = result.find('.notNull()', email_idx)
        self.assertGreater(notNull_idx, email_idx)

        # username is required
        username_idx = result.find("username: text( 'username'")
        notNull_idx = result.find('.notNull()', username_idx)
        self.assertGreater(notNull_idx, username_idx)

    def test_json_to_drizzle_optional_fields(self):
        """Test that optional fields don't have .notNull()"""
        result = json_to_drizzle(self.user_type)

        # name is optional - check it doesn't have notNull after it
        name_start = result.find("name: text( 'name' )")
        name_end = result.find('\n', name_start)
        name_line = result[name_start:name_end]
        self.assertNotIn('.notNull()', name_line)

    def test_json_to_drizzle_field_lengths(self):
        """Test that field lengths are correctly set"""
        result = json_to_drizzle(self.user_type)

        # email has length 50
        self.assertIn("email: text( 'email', { length: 50 }", result)

        # username has length 50
        self.assertIn("username: text( 'username', { length: 50 }", result)

        # domain has length 20
        self.assertIn("domain: text( 'domain', { length: 20 }", result)

    def test_json_to_drizzle_json_field(self):
        """Test that JSON fields are correctly formatted"""
        result = json_to_drizzle(self.user_type)

        # perms is JSON field
        self.assertIn("perms: text( 'perms', { mode: 'json' }", result)
        self.assertIn('.$type<any>()', result)

    def test_json_to_drizzle_integer_fields(self):
        """Test that integer fields are correctly typed"""
        result = json_to_drizzle(self.user_type)

        # level is integer
        self.assertIn("level: integer( 'level' )", result)

        # enabled is boolean
        self.assertIn("enabled: boolean( 'enabled' )", result)

    def test_json_to_drizzle_indexes(self):
        """Test that indexes are correctly generated"""
        result = json_to_drizzle(self.user_type)

        # Should have unique index on email
        self.assertIn("uniqueIndex( 'idx_users_email' ).on( table.email )", result)

        # Should have unique index on username
        self.assertIn("uniqueIndex( 'idx_users_username' ).on( table.username )", result)

        # Should have regular index on group (index type 'y')
        self.assertIn("index( 'idx_users_group' ).on( table.group )", result)

    def test_json_to_drizzle_field_comments(self):
        """Test that field comments are included"""
        result = json_to_drizzle(self.user_type)

        # Check for field descriptions
        self.assertIn('The user email', result)
        self.assertIn('User name', result)
        self.assertIn('User permissions', result)
        self.assertIn('Preferred language', result)

    def test_json_to_drizzle_table_comment(self):
        """Test that table description is in header comment"""
        result = json_to_drizzle(self.user_type)
        self.assertIn('The main user table', result)

    def test_json_to_drizzle_index_comments(self):
        """Test that index comments are included"""
        result = json_to_drizzle(self.user_type)

        # Should have comment for email index
        self.assertIn('Index on email field', result)

        # Should have comment for username index
        self.assertIn('Index on username field', result)

    def test_json_to_drizzle_custom_table_name(self):
        """Test that custom db_table is used"""
        # The user type has db_table set to 'users'
        result = json_to_drizzle(self.user_type)
        self.assertIn("sqliteTable( 'users'", result)

    def test_json_to_drizzle_type_inference(self):
        """Test that type inference export is correct"""
        result = json_to_drizzle(self.user_type)
        self.assertIn('export type User = typeof users.$inferSelect;', result)


class TestJsonToDrizzleEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios"""

    def test_minimal_type_definition(self):
        """Test with minimal type definition"""
        minimal_type = {
            'name': 'Simple',
            'fields': [
                {
                    'name': 'id',
                    'type': 'str',
                    'is_required': True,
                    'index': 'u'
                }
            ]
        }
        result = json_to_drizzle(minimal_type)
        self.assertIn('export const simples =', result)
        self.assertIn('export type Simple =', result)

    def test_type_without_db_table(self):
        """Test type without explicit db_table"""
        type_def = {
            'name': 'Product',
            'description': 'Product catalog',
            'fields': [
                {
                    'name': 'id',
                    'type': 'str',
                    'is_required': True,
                    'index': 'u'
                }
            ]
        }
        result = json_to_drizzle(type_def)
        # Should auto-pluralize to 'products'
        self.assertIn("sqliteTable( 'products'", result)

    def test_field_with_string_size(self):
        """Test field with size as string instead of int"""
        type_def = {
            'name': 'Test',
            'db_table': 'tests',
            'fields': [
                {
                    'name': 'code',
                    'type': 'str',
                    'size': '64',  # String instead of int
                    'is_required': False
                }
            ]
        }
        result = json_to_drizzle(type_def)
        self.assertIn('{ length: 64 }', result)

    def test_field_without_description(self):
        """Test field without description gets default comment"""
        type_def = {
            'name': 'Test',
            'db_table': 'tests',
            'fields': [
                {
                    'name': 'field1',
                    'type': 'str',
                    'is_required': False
                }
            ]
        }
        result = json_to_drizzle(type_def)
        self.assertIn('field1 field', result)


if __name__ == '__main__':
    unittest.main()
