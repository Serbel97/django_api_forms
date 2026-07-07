import typing

from django.forms import fields

from .fields import (
    AnyField,
    BooleanField,
    DictionaryField,
    EnumField,
    FieldList,
    FileField,
    FormField,
    FormFieldList,
    GeoJSONField,
    RRuleField,
)


def generate_form_schema(form_class: typing.Type) -> dict:
    """
    Generate an OpenAPI 3.0 Schema Object (as a plain dict) describing the JSON
    request body accepted by the given Form class.
    """
    mapping = {}
    meta = getattr(form_class, 'Meta', None)
    if isinstance(meta, type) and hasattr(meta, 'mapping'):
        mapping = {field_name: json_key for json_key, field_name in meta.mapping.items()}

    properties = {}
    required = []

    for name, field in form_class.base_fields.items():
        key = mapping.get(name, name)
        properties[key] = _field_to_schema(field)

        if field.required:
            required.append(key)

    schema = {
        'type': 'object',
        'properties': properties
    }

    if required:
        schema['required'] = required

    return schema


def _field_to_schema(field: fields.Field) -> dict:
    handler = _resolve_handler(type(field))
    schema = handler(field) if handler else {}

    if getattr(field, 'label', None):
        schema['title'] = str(field.label)
    if getattr(field, 'help_text', None):
        schema['description'] = str(field.help_text)

    return schema


def _resolve_handler(field_type: typing.Type) -> typing.Optional[typing.Callable]:
    for cls in field_type.__mro__:
        if cls in FIELD_SCHEMA_HANDLERS:
            return FIELD_SCHEMA_HANDLERS[cls]
    return None


def _enum_value_type(values: list) -> typing.Optional[str]:
    if all(isinstance(value, str) for value in values):
        return 'string'
    if all(isinstance(value, bool) for value in values):
        return 'boolean'
    if all(isinstance(value, int) for value in values):
        return 'integer'
    if all(isinstance(value, (int, float)) for value in values):
        return 'number'
    return None


def _string_schema(field: fields.Field, output_format: str = None) -> dict:
    schema = {'type': 'string'}

    if output_format:
        schema['format'] = output_format
    if getattr(field, 'min_length', None) is not None:
        schema['minLength'] = field.min_length
    if getattr(field, 'max_length', None) is not None:
        schema['maxLength'] = field.max_length

    return schema


def _numeric_schema(field: fields.Field, numeric_type: str) -> dict:
    schema = {'type': numeric_type}

    if getattr(field, 'min_value', None) is not None:
        schema['minimum'] = field.min_value
    if getattr(field, 'max_value', None) is not None:
        schema['maximum'] = field.max_value

    return schema


def _choice_schema(field: fields.ChoiceField) -> dict:
    values = []
    for value, label in field.choices:
        if isinstance(label, (list, tuple)):
            values.extend(item for item, _ in label)
        else:
            values.append(value)

    schema = {}
    value_type = _enum_value_type(values)
    if value_type:
        schema['type'] = value_type
    schema['enum'] = values

    return schema


def _enum_schema(field: EnumField) -> dict:
    values = [item.value for item in field.enum]

    schema = {}
    value_type = _enum_value_type(values)
    if value_type:
        schema['type'] = value_type
    schema['enum'] = values

    return schema


def _list_schema(field: FieldList) -> dict:
    schema = {
        'type': 'array',
        'items': _field_to_schema(field.field)
    }

    if field.min_length is not None:
        schema['minItems'] = field.min_length
    if field.max_length is not None:
        schema['maxItems'] = field.max_length

    return schema


def _form_schema(field: FormField) -> dict:
    return generate_form_schema(field.form)


def _form_list_schema(field: FormFieldList) -> dict:
    schema = {
        'type': 'array',
        'items': generate_form_schema(field.form)
    }

    if field.min_length is not None:
        schema['minItems'] = field.min_length
    if field.max_length is not None:
        schema['maxItems'] = field.max_length

    return schema


def _dictionary_schema(field: DictionaryField) -> dict:
    return {
        'type': 'object',
        'additionalProperties': _field_to_schema(field.value_field)
    }


FIELD_SCHEMA_HANDLERS = {
    fields.CharField: _string_schema,
    fields.EmailField: lambda field: _string_schema(field, 'email'),
    fields.URLField: lambda field: _string_schema(field, 'uri'),
    fields.UUIDField: lambda field: _string_schema(field, 'uuid'),
    fields.DateTimeField: lambda field: _string_schema(field, 'date-time'),
    fields.DateField: lambda field: _string_schema(field, 'date'),
    fields.TimeField: lambda field: _string_schema(field, 'time'),
    fields.DurationField: lambda field: _string_schema(field, 'duration'),
    fields.IntegerField: lambda field: _numeric_schema(field, 'integer'),
    fields.FloatField: lambda field: _numeric_schema(field, 'number'),
    fields.DecimalField: lambda field: _numeric_schema(field, 'number'),
    fields.BooleanField: lambda field: {'type': 'boolean'},
    fields.ChoiceField: _choice_schema,
    BooleanField: lambda field: {'type': 'boolean'},
    EnumField: _enum_schema,
    FieldList: _list_schema,
    FormField: _form_schema,
    FormFieldList: _form_list_schema,
    DictionaryField: _dictionary_schema,
    FileField: lambda field: _string_schema(field, 'byte'),
    RRuleField: lambda field: _string_schema(field),
    GeoJSONField: lambda field: {'type': 'object'},
    AnyField: lambda field: {},
}
