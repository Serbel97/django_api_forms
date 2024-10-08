import copy


class BaseStrategy:
    def __call__(self, field, obj, key: str, value):
        setattr(obj, key, value)


class AliasStrategy(BaseStrategy):
    def __init__(self, property_name: str):
        self._property_name = property_name

    def __call__(self, field, obj, key: str, value):
        setattr(obj, self._property_name, value)


class IgnoreStrategy(BaseStrategy):
    def __call__(self, field, obj, key: str, value):
        pass


class ModelChoiceFieldStrategy(BaseStrategy):

    """
    We need to change key postfix if there is a ModelChoiceField (because of _id etc.)
    We always try to assign whole object instance, for example:
    artis_id is normalized as Artist model, but it have to be assigned to artist model property
    because artist_id in model has different type (for example int if your are using int primary keys)
    If you are still confused (sorry), try to check docs
    """
    def __call__(self, field, obj, key: str, value):
        model_key = key
        if field.to_field_name:
            postfix_to_remove = f"_{field.to_field_name}"
        else:
            postfix_to_remove = "_id"
        if key.endswith(postfix_to_remove):
            model_key = key[:-len(postfix_to_remove)]
        setattr(obj, model_key, value)


class FormFieldStrategy(BaseStrategy):
    def __call__(self, field, obj, key: str, value):
        model = field.model
        if model:
            from django_api_forms.settings import Settings

            model = model()
            form = field.form

            form.cleaned_data = value
            form.fields = copy.deepcopy(getattr(form, 'base_fields'))
            form.settings = Settings()
            form.errors = None

            populated_model = form.populate(form, model)

            setattr(obj, key, populated_model)
