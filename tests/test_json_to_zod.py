#!/usr/bin/env python3

"""
Unit tests for json_to_zod module
"""

import json
import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../flow2code')))

from lib.json_to_zod import (
    json_to_zod,
    _get_zod_type,
    _add_validation_constraints,
    _format_field_comment
)


class TestJsonToZodHelpers(unittest.TestCase):
    """Test helper functions"""

    def test_get_zod_type_string(self):
        """Test string type mapping"""
        zod_type = _get_zod_type('str', False, True)
        self.assertEqual(zod_type, 'z.string()')

    def test_get_zod_type_number(self):
        """Test number type mapping with coerce"""
        zod_type = _get_zod_type('num', False, True)
        self.assertEqual(zod_type, 'z.coerce.number()')

    def test_get_zod_type_float(self):
        """Test float type mapping with coerce"""
        zod_type = _get_zod_type('float', False, True)
        self.assertEqual(zod_type, 'z.coerce.number()')

    def test_get_zod_type_boolean(self):
        """Test boolean type mapping with preprocess"""
        zod_type = _get_zod_type('boolean', False, True)
        # Should use preprocess to handle string 'true'/'false' conversion
        self.assertIn('z.preprocess', zod_type)
        self.assertIn('z.boolean()', zod_type)
        self.assertIn("val === 'true'", zod_type)

    def test_get_zod_type_date(self):
        """Test date type mapping"""
        zod_type = _get_zod_type('date', False, True)
        self.assertEqual(zod_type, 'z.string()')

    def test_get_zod_type_datetime(self):
        """Test datetime type mapping with coerce"""
        zod_type = _get_zod_type('datetime', False, True)
        self.assertEqual(zod_type, 'z.coerce.date()')

    def test_get_zod_type_json(self):
        """Test JSON type mapping"""
        zod_type = _get_zod_type('json', False, False)
        self.assertEqual(zod_type, 'z.any()')

    def test_add_validation_constraints_string_min(self):
        """Test string min length constraint"""
        field = {
            'name': 'username',
            'type': 'str',
            'min_length': 3,
            'size': 0
        }
        result = _add_validation_constraints('z.string()', field)
        self.assertIn('.min( 3', result)
        self.assertIn('Username is required', result)

    def test_add_validation_constraints_string_max(self):
        """Test string max length constraint"""
        field = {
            'name': 'email',
            'type': 'str',
            'min_length': 0,
            'size': 50
        }
        result = _add_validation_constraints('z.string()', field)
        self.assertIn('.max( 50', result)
        self.assertIn('Email must be at most 50 characters', result)

    def test_add_validation_constraints_string_both(self):
        """Test string min and max constraints"""
        field = {
            'name': 'name',
            'type': 'str',
            'min_length': 1,
            'size': 100
        }
        result = _add_validation_constraints('z.string()', field)
        self.assertIn('.min( 1', result)
        self.assertIn('.max( 100', result)

    def test_add_validation_constraints_number_range(self):
        """Test number min/max constraints"""
        field = {
            'name': 'weight',
            'type': 'number',
            'min_length': 0,
            'size': 10
        }
        result = _add_validation_constraints('z.coerce.number()', field)
        self.assertIn('.max( 10 )', result)

    def test_add_validation_constraints_string_size(self):
        """Test with string size value"""
        field = {
            'name': 'code',
            'type': 'str',
            'size': '64',  # String instead of int
            'min_length': 0
        }
        result = _add_validation_constraints('z.string()', field)
        self.assertIn('.max( 64', result)

    def test_format_field_comment_required(self):
        """Test field comment for required field"""
        field = {
            'name': 'name',
            'type': 'str',
            'is_array': False,
            'is_required': True,
            'description': 'Tag name',
            'size': 0,
            'min_length': 1
        }
        result = _format_field_comment(field)
        self.assertEqual(len(result), 1)
        self.assertIn('name', result[0])
        self.assertIn('Tag name', result[0])
        self.assertIn('required', result[0])
        self.assertIn('min 1 chars', result[0])

    def test_format_field_comment_optional(self):
        """Test field comment for optional field"""
        field = {
            'name': 'description',
            'type': 'str',
            'is_array': False,
            'is_required': False,
            'description': 'Tag description',
            'size': 0,
            'min_length': 0
        }
        result = _format_field_comment(field)
        self.assertIn('[str]', result[0])  # Optional type annotation
        self.assertIn('description', result[0])

    def test_format_field_comment_array(self):
        """Test field comment for array field"""
        field = {
            'name': 'tags',
            'type': 'str',
            'is_array': True,
            'is_required': False,
            'description': 'User tags',
            'size': 0,
            'min_length': 0
        }
        result = _format_field_comment(field)
        self.assertIn('str[]', result[0])  # Array type annotation
        self.assertIn('[str[]]', result[0])  # Optional array

    def test_format_field_comment_with_size(self):
        """Test field comment with size constraint"""
        field = {
            'name': 'email',
            'type': 'str',
            'is_array': False,
            'is_required': True,
            'description': 'User email',
            'size': 50,
            'min_length': 0
        }
        result = _format_field_comment(field)
        self.assertIn('max 50 chars', result[0])


class TestJsonToZodConverter(unittest.TestCase):
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

    def test_json_to_zod_output_structure(self):
        """Test that output has expected structure"""
        result = json_to_zod(self.user_type)

        # Check for essential elements
        self.assertIn('const UserSchema = z.object( {', result)
        self.assertIn('/**', result)  # Has JSDoc comments
        self.assertIn('*/', result)
        self.assertIn('@property', result)  # Has property documentation

    def test_json_to_zod_schema_name(self):
        """Test that schema name is correctly generated"""
        result = json_to_zod(self.user_type)
        self.assertIn('const UserSchema = z.object( {', result)

    def test_json_to_zod_header_comment(self):
        """Test that header comment includes description"""
        result = json_to_zod(self.user_type)
        self.assertIn('The main user table', result)

    def test_json_to_zod_required_string_fields(self):
        """Test that required string fields have validation"""
        result = json_to_zod(self.user_type)

        # id is required
        self.assertIn('id: z.string()', result)
        self.assertNotIn('id: z.string().optional()', result)

        # email is required with size constraint
        self.assertIn('email: z.string()', result)
        self.assertIn('.max( 50', result)

    def test_json_to_zod_optional_fields(self):
        """Test that optional fields have .optional()"""
        result = json_to_zod(self.user_type)

        # name is optional
        self.assertIn('name: z.string().optional()', result)

        # description might not be in user type, but any optional field should have it
        # Let's check lastname which is optional
        self.assertIn('lastname: z.string().optional()', result)

    def test_json_to_zod_number_fields(self):
        """Test that number fields use coerce"""
        result = json_to_zod(self.user_type)

        # level is a number field
        self.assertIn('level: z.coerce.number()', result)

    def test_json_to_zod_boolean_fields(self):
        """Test that boolean fields use preprocess for string conversion"""
        result = json_to_zod(self.user_type)

        # enabled is a boolean field - should use preprocess
        self.assertIn('enabled: z.preprocess', result)
        self.assertIn('z.boolean()', result)

    def test_json_to_zod_array_fields(self):
        """Test that array fields have .array()"""
        result = json_to_zod(self.user_type)

        # tags is an array field
        self.assertIn('tags: z.string().array().optional()', result)

    def test_json_to_zod_json_fields(self):
        """Test that JSON fields use z.any()"""
        result = json_to_zod(self.user_type)

        # perms is a JSON field
        self.assertIn('perms: z.any().optional()', result)

    def test_json_to_zod_field_comments(self):
        """Test that field comments are included"""
        result = json_to_zod(self.user_type)

        # Check for field descriptions in comments
        self.assertIn('The user email', result)
        self.assertIn('User name', result)
        self.assertIn('User permissions', result)
        self.assertIn('Preferred language', result)

    def test_json_to_zod_size_constraints(self):
        """Test that size constraints are applied"""
        result = json_to_zod(self.user_type)

        # email has max size 50
        email_idx = result.find('email: z.string()')
        max_idx = result.find('.max( 50', email_idx)
        self.assertGreater(max_idx, email_idx)

        # username has max size 50
        username_idx = result.find('username: z.string()')
        max_idx = result.find('.max( 50', username_idx)
        self.assertGreater(max_idx, username_idx)

    def test_json_to_zod_date_fields(self):
        """Test that date fields are correctly typed"""
        result = json_to_zod(self.user_type)

        # deleted is a date field
        self.assertIn('deleted: z.string().optional()', result)


class TestJsonToZodEdgeCases(unittest.TestCase):
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
                    'is_array': False,
                    'size': 0,
                    'min_length': 0
                }
            ]
        }
        result = json_to_zod(minimal_type)
        self.assertIn('const SimpleSchema = z.object( {', result)
        self.assertIn('id: z.string()', result)

    def test_type_without_description(self):
        """Test type without description gets default comment"""
        type_def = {
            'name': 'Product',
            'fields': [
                {
                    'name': 'name',
                    'type': 'str',
                    'is_required': True,
                    'is_array': False,
                    'size': 0,
                    'min_length': 0
                }
            ]
        }
        result = json_to_zod(type_def)
        self.assertIn('Schema for Product', result)

    def test_field_without_description(self):
        """Test field without description gets default comment"""
        type_def = {
            'name': 'Test',
            'fields': [
                {
                    'name': 'field1',
                    'type': 'str',
                    'is_required': False,
                    'is_array': False,
                    'size': 0,
                    'min_length': 0
                }
            ]
        }
        result = json_to_zod(type_def)
        self.assertIn('field1 field', result)

    def test_coerce_number_with_default(self):
        """Test number field with default value"""
        type_def = {
            'name': 'Tag',
            'fields': [
                {
                    'name': 'weight',
                    'type': 'number',
                    'is_required': False,
                    'is_array': False,
                    'size': 10,
                    'min_length': 0
                }
            ]
        }
        result = json_to_zod(type_def)
        self.assertIn('weight: z.coerce.number()', result)
        self.assertIn('.default( 1.0 )', result)

    def test_all_field_types(self):
        """Test all supported field types"""
        type_def = {
            'name': 'AllTypes',
            'fields': [
                {'name': 'str_field', 'type': 'str', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'num_field', 'type': 'num', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'float_field', 'type': 'float', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'bool_field', 'type': 'boolean', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'date_field', 'type': 'date', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'datetime_field', 'type': 'datetime', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
                {'name': 'json_field', 'type': 'json', 'is_required': False, 'is_array': False, 'size': 0, 'min_length': 0},
            ]
        }
        result = json_to_zod(type_def)

        self.assertIn('str_field: z.string().optional()', result)
        self.assertIn('num_field: z.coerce.number().optional()', result)
        self.assertIn('float_field: z.coerce.number().optional()', result)
        # Boolean fields use preprocess instead of coerce
        self.assertIn('bool_field: z.preprocess', result)
        self.assertIn('z.boolean() ).optional()', result)
        self.assertIn('date_field: z.string().optional()', result)
        self.assertIn('datetime_field: z.coerce.date().optional()', result)
        self.assertIn('json_field: z.any().optional()', result)


if __name__ == '__main__':
    unittest.main()
