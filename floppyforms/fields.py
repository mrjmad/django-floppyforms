import django
from django import forms
import decimal

from .widgets import (TextInput, HiddenInput, CheckboxInput, Select,
                      ClearableFileInput, SelectMultiple, DateInput,
                      DateTimeInput, TimeInput, URLInput, NumberInput,
                      EmailInput, NullBooleanSelect, SlugInput, IPAddressInput,
                      SplitDateTimeWidget, SplitHiddenDateTimeWidget,
                      MultipleHiddenInput)

__all__ = (
    'Field', 'CharField', 'IntegerField', 'DateField', 'TimeField',
    'DateTimeField', 'EmailField', 'FileField', 'ImageField', 'URLField',
    'BooleanField', 'NullBooleanField', 'ChoiceField', 'MultipleChoiceField',
    'FloatField', 'DecimalField', 'SlugField', 'RegexField',
    'GenericIPAddressField', 'TypedChoiceField', 'FilePathField',
    'TypedMultipleChoiceField', 'ComboField', 'MultiValueField',
    'SplitDateTimeField',
)
if django.VERSION < (1, 9):
    __all__ += ('IPAddressField',)


class FieldMixin(object):
    widget = TextInput
    hidden_widget = HiddenInput


class Field(FieldMixin, forms.Field):
    widget = TextInput
    hidden_widget = HiddenInput


class CharField(FieldMixin, forms.CharField):
    widget = TextInput

    def widget_attrs(self, widget):
        attrs = super(CharField, self).widget_attrs(widget)
        if attrs is None:
            attrs = {}
        if self.max_length is not None and isinstance(widget, (TextInput, HiddenInput)):
            # The HTML attribute is maxlength, not max_length.
            attrs.update({'maxlength': str(self.max_length)})
        return attrs


class BooleanField(FieldMixin, forms.BooleanField):
    widget = CheckboxInput


class NullBooleanField(FieldMixin, forms.NullBooleanField):
    widget = NullBooleanSelect


class ChoiceField(FieldMixin, forms.ChoiceField):
    widget = Select


class TypedChoiceField(FieldMixin, forms.TypedChoiceField):
    widget = Select


class FilePathField(FieldMixin, forms.FilePathField):
    widget = Select


class FileField(FieldMixin, forms.FileField):
    widget = ClearableFileInput


class ImageField(FieldMixin, forms.ImageField):
    widget = ClearableFileInput


class MultipleChoiceField(FieldMixin, forms.MultipleChoiceField):
    widget = SelectMultiple
    hidden_widget = MultipleHiddenInput


class TypedMultipleChoiceField(MultipleChoiceField,
                               forms.TypedMultipleChoiceField):
    pass


class DateField(FieldMixin, forms.DateField):
    widget = DateInput


class DateTimeField(FieldMixin, forms.DateTimeField):
    widget = DateTimeInput


class TimeField(FieldMixin, forms.TimeField):
    widget = TimeInput


class FloatField(FieldMixin, forms.FloatField):
    widget = NumberInput

    def widget_attrs(self, widget):
        attrs = super(FloatField, self).widget_attrs(widget) or {}
        if self.min_value is not None:
            attrs['min'] = self.min_value
        if self.max_value is not None:
            attrs['max'] = self.max_value
        if 'step' not in widget.attrs:
            attrs.setdefault('step', 'any')
        return attrs


class IntegerField(FieldMixin, forms.IntegerField):
    widget = NumberInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', NumberInput if not kwargs.get('localize') else self.widget)
        super(IntegerField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(IntegerField, self).widget_attrs(widget) or {}
        if self.min_value is not None:
            attrs['min'] = self.min_value
        if self.max_value is not None:
            attrs['max'] = self.max_value
        return attrs


class DecimalField(FieldMixin, forms.DecimalField):
    widget = NumberInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', NumberInput if not kwargs.get('localize') else self.widget)
        super(DecimalField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(DecimalField, self).widget_attrs(widget) or {}
        if self.min_value is not None:
            attrs['min'] = self.min_value
        if self.max_value is not None:
            attrs['max'] = self.max_value
        if self.decimal_places is not None:
            attrs['step'] = decimal.Decimal('0.1') ** self.decimal_places
        return attrs


class EmailField(FieldMixin, forms.EmailField):
    widget = EmailInput


class URLField(FieldMixin, forms.URLField):
    widget = URLInput


class SlugField(FieldMixin, forms.SlugField):
    widget = SlugInput


class RegexField(FieldMixin, forms.RegexField):
    widget = TextInput

    def __init__(self, regex, js_regex=None, max_length=None, min_length=None, error_message=None, **kwargs):
        self.js_regex = js_regex

        if error_message is not None:
            error_messages = kwargs.get('error_messages') or {}
            error_messages['invalid'] = error_message
            kwargs['error_messages'] = error_messages

        super(RegexField, self).__init__(regex,
                                         max_length=max_length,
                                         min_length=min_length,
                                         **kwargs)

    def widget_attrs(self, widget):
        attrs = super(RegexField, self).widget_attrs(widget) or {}
        if self.js_regex is not None:
            attrs['pattern'] = self.js_regex
        return attrs


if django.VERSION < (1, 9):
    class IPAddressField(FieldMixin, forms.IPAddressField):
        widget = IPAddressInput


class GenericIPAddressField(FieldMixin, forms.GenericIPAddressField):
    pass


class ComboField(FieldMixin, forms.ComboField):
    pass


class MultiValueField(FieldMixin, forms.MultiValueField):
    pass


class SplitDateTimeField(FieldMixin, forms.SplitDateTimeField):
    widget = SplitDateTimeWidget
    hidden_widget = SplitHiddenDateTimeWidget

    def __init__(self, *args, **kwargs):
        super(SplitDateTimeField, self).__init__(*args, **kwargs)
        for widget in self.widget.widgets:
            widget.is_required = self.required
