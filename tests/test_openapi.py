from enum import Enum

from django.forms import fields
from django.test import SimpleTestCase

from django_api_forms import (
    AnyField,
    BooleanField,
    DictionaryField,
    EnumField,
    FieldList,
    FileField,
    Form,
    FormField,
    FormFieldList,
    GeoJSONField,
    ImageField,
    RRuleField,
)
from django_api_forms.openapi import generate_form_schema


class AlbumType(Enum):
    CD = 'cd'
    VINYL = 'vinyl'


class ScalarFieldsTests(SimpleTestCase):
    def test_char_field(self):
        class MyForm(Form):
            title = fields.CharField(required=True, min_length=2, max_length=100)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['type'], 'object')
        self.assertEqual(
            schema['properties']['title'],
            {'type': 'string', 'minLength': 2, 'maxLength': 100}
        )
        self.assertEqual(schema['required'], ['title'])

    def test_numeric_fields(self):
        class MyForm(Form):
            year = fields.IntegerField(required=False, min_value=1900, max_value=2100)
            rating = fields.FloatField(required=False)
            price = fields.DecimalField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['year'],
            {'type': 'integer', 'minimum': 1900, 'maximum': 2100}
        )
        self.assertEqual(schema['properties']['rating'], {'type': 'number'})
        self.assertEqual(schema['properties']['price'], {'type': 'number'})
        self.assertNotIn('required', schema)

    def test_boolean_fields(self):
        class MyForm(Form):
            django_flag = fields.BooleanField(required=False)
            api_flag = BooleanField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['django_flag'], {'type': 'boolean'})
        self.assertEqual(schema['properties']['api_flag'], {'type': 'boolean'})

    def test_string_format_fields(self):
        class MyForm(Form):
            created_at = fields.DateTimeField(required=False)
            birthday = fields.DateField(required=False)
            alarm = fields.TimeField(required=False)
            duration = fields.DurationField(required=False)
            uuid = fields.UUIDField(required=False)
            email = fields.EmailField(required=False)
            website = fields.URLField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['created_at'], {'type': 'string', 'format': 'date-time'})
        self.assertEqual(schema['properties']['birthday'], {'type': 'string', 'format': 'date'})
        self.assertEqual(schema['properties']['alarm'], {'type': 'string', 'format': 'time'})
        self.assertEqual(schema['properties']['duration'], {'type': 'string', 'format': 'duration'})
        self.assertEqual(schema['properties']['uuid'], {'type': 'string', 'format': 'uuid'})
        self.assertEqual(
            schema['properties']['email'],
            {'type': 'string', 'format': 'email', 'maxLength': fields.EmailField().max_length}
        )
        self.assertEqual(schema['properties']['website'], {'type': 'string', 'format': 'uri'})

    def test_choice_field(self):
        class MyForm(Form):
            genre = fields.ChoiceField(required=False, choices=(('rock', 'Rock'), ('punk', 'Punk')))

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['genre'],
            {'type': 'string', 'enum': ['rock', 'punk']}
        )

    def test_title_and_description(self):
        class MyForm(Form):
            name = fields.CharField(required=False, label='Name', help_text='Artist name')

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['name']['title'], 'Name')
        self.assertEqual(schema['properties']['name']['description'], 'Artist name')


class LibraryFieldsTests(SimpleTestCase):
    def test_enum_field(self):
        class MyForm(Form):
            type = EnumField(enum=AlbumType, required=True)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['type'],
            {'type': 'string', 'enum': ['cd', 'vinyl']}
        )

    def test_field_list(self):
        class MyForm(Form):
            genres = FieldList(field=fields.CharField(max_length=30), min_length=1, max_length=10, required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['genres'],
            {
                'type': 'array',
                'items': {'type': 'string', 'maxLength': 30},
                'minItems': 1,
                'maxItems': 10
            }
        )

    def test_form_field(self):
        class ArtistForm(Form):
            name = fields.CharField(required=True, max_length=100)
            members = fields.IntegerField(required=False)

        class MyForm(Form):
            artist = FormField(form=ArtistForm, required=True)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['artist'],
            {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'maxLength': 100},
                    'members': {'type': 'integer'}
                },
                'required': ['name']
            }
        )
        self.assertEqual(schema['required'], ['artist'])

    def test_form_field_list(self):
        class SongForm(Form):
            title = fields.CharField(required=True, max_length=100)

        class MyForm(Form):
            songs = FormFieldList(form=SongForm, min_length=1, required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['songs'],
            {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'maxLength': 100}
                    },
                    'required': ['title']
                },
                'minItems': 1
            }
        )

    def test_dictionary_field(self):
        class MyForm(Form):
            metadata = DictionaryField(value_field=fields.DateTimeField(), required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(
            schema['properties']['metadata'],
            {
                'type': 'object',
                'additionalProperties': {'type': 'string', 'format': 'date-time'}
            }
        )

    def test_file_fields(self):
        class MyForm(Form):
            attachment = FileField(required=False)
            avatar = ImageField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['attachment'], {'type': 'string', 'format': 'byte'})
        self.assertEqual(schema['properties']['avatar'], {'type': 'string', 'format': 'byte'})

    def test_rrule_and_geojson_fields(self):
        class MyForm(Form):
            recurrence = RRuleField(required=False)
            location = GeoJSONField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['recurrence'], {'type': 'string'})
        self.assertEqual(schema['properties']['location'], {'type': 'object'})

    def test_any_field(self):
        class MyForm(Form):
            payload = AnyField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['payload'], {})

    def test_unknown_field_fallback(self):
        class WeirdField(fields.Field):
            pass

        class MyForm(Form):
            weird = WeirdField(required=False)

        schema = generate_form_schema(MyForm)

        self.assertEqual(schema['properties']['weird'], {})


class MetaMappingTests(SimpleTestCase):
    def test_mapping_reverses_property_names(self):
        class ArtistForm(Form):
            class Meta:
                mapping = {
                    '_name': 'name'
                }

            name = fields.CharField(required=True, max_length=100)
            members = fields.IntegerField(required=False)

        schema = generate_form_schema(ArtistForm)

        self.assertIn('_name', schema['properties'])
        self.assertNotIn('name', schema['properties'])
        self.assertEqual(schema['required'], ['_name'])
        self.assertIn('members', schema['properties'])


class NestedFormTests(SimpleTestCase):
    def test_complete_nested_form(self):
        class ArtistForm(Form):
            name = fields.CharField(required=True, max_length=100)
            genres = FieldList(field=fields.CharField(max_length=30), required=False)
            members = fields.IntegerField(required=False)

        class AlbumForm(Form):
            title = fields.CharField(required=True, max_length=100)
            year = fields.IntegerField(required=True)
            artist = FormField(form=ArtistForm, required=True)
            type = EnumField(enum=AlbumType, required=True)
            metadata = DictionaryField(value_field=fields.DateTimeField(), required=False)

        schema = generate_form_schema(AlbumForm)

        self.assertEqual(schema['type'], 'object')
        self.assertEqual(schema['required'], ['title', 'year', 'artist', 'type'])
        self.assertEqual(schema['properties']['artist']['type'], 'object')
        self.assertEqual(schema['properties']['artist']['required'], ['name'])
