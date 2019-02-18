import datetime
from itertools import chain
import re
import warnings

from django import forms
import django
from django.conf import settings
from django.forms.widgets import FILE_INPUT_CONTRADICTION
from django.template import loader
from django.utils import datetime_safe, formats, six
from django.utils.dates import MONTHS
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.translation import ugettext_lazy as _

from .compat import MULTIVALUE_DICT_TYPES, flatten_contexts


try:
    from django.forms.utils import to_current_timezone
except ImportError:
    # Fall back to old module name for Django <= 1.5
    from django.forms.util import to_current_timezone


RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


__all__ = (
    'TextInput', 'PasswordInput', 'HiddenInput', 'ClearableFileInput',
    'FileInput', 'DateInput', 'DateTimeInput', 'TimeInput', 'Textarea',
    'CheckboxInput', 'Select', 'NullBooleanSelect', 'SelectMultiple',
    'RadioSelect', 'CheckboxSelectMultiple', 'SearchInput', 'RangeInput',
    'ColorInput', 'EmailInput', 'URLInput', 'PhoneNumberInput', 'NumberInput',
    'IPAddressInput', 'MultiWidget', 'Widget', 'SplitDateTimeWidget',
    'SplitHiddenDateTimeWidget', 'MultipleHiddenInput', 'SelectDateWidget',
    'SlugInput',
)

if django.VERSION < (1, 11):
    class TemplateBasedWidget(object):
        is_required = False
        # This attribute is used to inject a surrounding context in the
        # floppyforms templatetags, when rendered inside a complete form.
        context_instance = None

        def get_context(self, name, value, attrs):
            context = {}
            context['widget'] = {
                'name': name,
                'is_hidden': self.is_hidden,
                'required': self.is_required,
                'value': self.format_value(value),
                'attrs': self.build_widget_attrs(self.attrs, attrs),
                'template_name': self.template_name,
            }

            return context

        def build_widget_attrs(self, base_attrs, extra_attrs=None):
            attrs = base_attrs.copy()
            if extra_attrs is not None:
                attrs.update(extra_attrs)
            return attrs

        def render(self, name, value, attrs=None, **kwargs):
            """
            Returns this Widget rendered as HTML, as a Unicode string.
            """
            template_name = kwargs.pop('template_name', None)
            if template_name is None:
                template_name = self.template_name

            context = self.get_context(name, value, attrs=attrs)
            context['template_name'] = template_name

            return self._render(template_name, context, renderer=None)

        def _render(self, template_name, context, renderer=None):
            context = flatten_contexts(self.context_instance, context)
            html = loader.render_to_string(template_name, context)
            return html

        def format_value(self, value):
            """
            Return a value as it should appear when rendered in a template.
            """
            if value == '' or value is None:
                return None
            if self.is_localized:
                return formats.localize_input(value)
            return force_text(value)
else:
    class TemplateBasedWidget(object):
        # This attribute is used to inject a surrounding context in the
        # floppyforms templatetags, when rendered inside a complete form.
        context_instance = None

        def __init__(self, *args, **kwargs):
            warnings.warn("""
                The floppyforms widgets are now deprecated. Please use django's
                template-based widgets instead.
                """, DeprecationWarning, stacklevel=2)

            super(TemplateBasedWidget, self).__init__(*args, **kwargs)

        def _render(self, template_name, context, renderer=None):
            print(self.is_required, context['widget']['required'], context['widget']['attrs'])
            context = flatten_contexts(self.context_instance, context)
            return super(TemplateBasedWidget, self)._render(
                template_name, context, renderer)


class Widget(TemplateBasedWidget, forms.Widget):
    # Ignore required attribute in Django >= 1.10 or it will be rendered
    # twice
    def use_required_attribute(self, initial):
        return False


class Input(Widget):
    template_name = 'floppyforms/input.html'
    input_type = None
    datalist = None

    def __init__(self, *args, **kwargs):
        datalist = kwargs.pop('datalist', None)
        if datalist is not None:
            self.datalist = datalist
        template_name = kwargs.pop('template_name', None)
        if template_name is not None:
            self.template_name = template_name
        super(Input, self).__init__(*args, **kwargs)

    def format_value(self, value):
        if value is None:
            value = ''

        if self.is_localized:
            value = formats.localize_input(value)

        return force_text(value)

    def get_context(self, name, value, attrs=None):
        context = super(Input, self).get_context(name, value, attrs)

        widget_ctx = context['widget']
        widget_ctx['type'] = self.input_type

        # True is injected in the context to allow stricter comparisons
        # for widget attrs. See #25.
        context['True'] = True

        for key, attr in widget_ctx['attrs'].items():
            if attr and not isinstance(attr, bool):
                widget_ctx['attrs'][key] = str(attr)

        if self.datalist is not None:
            context['datalist'] = self.datalist

        return context


class TextInput(Input):
    template_name = 'floppyforms/text.html'
    input_type = 'text'

    def __init__(self, *args, **kwargs):
        if kwargs.get('attrs', None) is not None:
            self.input_type = kwargs['attrs'].pop('type', self.input_type)
        super(TextInput, self).__init__(*args, **kwargs)


class PasswordInput(TextInput):
    template_name = 'floppyforms/password.html'
    input_type = 'password'

    def __init__(self, attrs=None, render_value=False):
        super(PasswordInput, self).__init__(attrs)
        self.render_value = render_value

    def get_context(self, name, value, attrs=None):
        if not self.render_value:
            value = None

        return super(PasswordInput, self).get_context(name, value, attrs)


class HiddenInput(Input):
    template_name = 'floppyforms/hidden.html'
    input_type = 'hidden'


class MultipleHiddenInput(HiddenInput):
    template_name = 'floppyforms/multiwidget.html'

    """<input type="hidden"> for fields that have a list of values"""
    def __init__(self, attrs=None):
        super(MultipleHiddenInput, self).__init__(attrs)

    def get_context(self, name, value, attrs=None):
        context = super(MultipleHiddenInput, self).get_context(name, value, attrs=attrs)

        if value is not None:
            final_attrs = context['widget']['attrs']
            id_ = final_attrs.get('id', None)
            inputs = []

            for i, v in enumerate(value):
                input_attrs = final_attrs.copy()
                if id_:
                    input_attrs['id'] = '%s_%s' % (id_, i)
                input_ = HiddenInput()
                input_.is_required = self.is_required
                inputs.append(input_.get_context(name, force_text(v), input_attrs)['widget'])

            context['widget']['subwidgets'] = inputs

        return context

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MULTIVALUE_DICT_TYPES):
            return data.getlist(name)
        return data.get(name, None)


class SlugInput(TextInput):
    template_name = 'floppyforms/slug.html'

    """<input type="text"> validating slugs with a pattern"""
    def get_context(self, name, value, attrs):
        context = super(SlugInput, self).get_context(name, value, attrs)
        context['widget']['attrs']['pattern'] = r"[-\w]+"
        return context


class IPAddressInput(TextInput):
    template_name = 'floppyforms/ipaddress.html'

    """<input type="text"> validating IP addresses with a pattern"""
    ip_pattern = (r"(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25"
                  r"[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}")

    def get_context(self, name, value, attrs):
        context = super(IPAddressInput, self).get_context(name, value, attrs)
        context['widget']['attrs']['pattern'] = self.ip_pattern
        return context


class FileInput(Input):
    template_name = 'floppyforms/file.html'
    input_type = 'file'
    needs_multipart_form = True
    omit_value = True

    def get_context(self, name, value, attrs=None):
        # File inputs can't render an existing value if it's not saved
        if self.omit_value:
            value = None

        return super(FileInput, self).get_context(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        return files.get(name, None)


class ClearableFileInput(FileInput):
    template_name = 'floppyforms/clearable_input.html'
    omit_value = False

    initial_text = _('Currently')
    input_text = _('Change')
    clear_checkbox_label = _('Clear')

    def clear_checkbox_name(self, name):
        return name + '-clear'

    def clear_checkbox_id(self, name):
        return name + '_id'

    def get_context(self, name, value, attrs):
        context = super(ClearableFileInput, self).get_context(name, value,
                                                              attrs)
        ccb_name = self.clear_checkbox_name(name)
        context.update({
            'clear_checkbox_label': self.clear_checkbox_label,
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'checkbox_name': ccb_name,
            'checkbox_id': self.clear_checkbox_id(ccb_name),
        })
        return context

    def value_from_datadict(self, data, files, name):
        upload = super(ClearableFileInput, self).value_from_datadict(
            data, files, name
        )
        if not self.is_required and CheckboxInput().value_from_datadict(
            data, files, self.clear_checkbox_name(name)
        ):
            if upload:
                return FILE_INPUT_CONTRADICTION
            return False
        return upload

    def format_value(self, value):
        # If the value is falsy, then it might be a file instance with no file
        # associated with. That can happen if you get the value from a
        # models.ImageField that is set to None. In that case we just return
        # None. Otherwise calls in the template like {{ value.url }} will raise
        # a ValueError.
        if not value:
            return None
        return value


class Textarea(Input):
    template_name = 'floppyforms/textarea.html'
    rows = 10
    cols = 40

    def __init__(self, attrs=None):
        default_attrs = {'cols': self.cols, 'rows': self.rows}
        if attrs:
            default_attrs.update(attrs)
        super(Textarea, self).__init__(default_attrs)

    def format_value(self, value):
        if value is None:
            return ''

        return conditional_escape(force_text(value))


class DateInput(Input):
    template_name = 'floppyforms/date.html'
    input_type = 'date'
    supports_microseconds = False

    def __init__(self, attrs=None, format=None):
        super(DateInput, self).__init__(attrs)
        # We hardcode the format here as the HTML5 input type="date" only
        # accepts the ISO date format. See issue #115 for details:
        # https://github.com/gregmuellegger/django-floppyforms/issues/115
        self.format = '%Y-%m-%d'

    def format_value(self, value):
        if hasattr(value, 'strftime'):
            value = datetime_safe.new_date(value)
            return value.strftime(self.format)
        return value


class DateTimeInput(Input):
    template_name = 'floppyforms/datetime.html'
    input_type = 'datetime'
    supports_microseconds = False

    def __init__(self, attrs=None, format=None):
        super(DateTimeInput, self).__init__(attrs)
        if format:
            self.format = format
            self.manual_format = True
        else:
            self.format = formats.get_format('DATETIME_INPUT_FORMATS')[0]
            self.manual_format = False

    def format_value(self, value):
        if hasattr(value, 'strftime'):
            value = datetime_safe.new_datetime(value)
            return value.strftime(self.format)
        return value


class TimeInput(Input):
    template_name = 'floppyforms/time.html'
    input_type = 'time'
    supports_microseconds = False

    def __init__(self, attrs=None, format=None):
        super(TimeInput, self).__init__(attrs)
        if format:
            self.format = format
            self.manual_format = True
        else:
            self.format = formats.get_format('TIME_INPUT_FORMATS')[0]
            self.manual_format = False

    def format_value(self, value):
        if hasattr(value, 'strftime'):
            return value.strftime(self.format)
        return value


class SearchInput(Input):
    template_name = 'floppyforms/search.html'
    input_type = 'search'


class EmailInput(TextInput):
    template_name = 'floppyforms/email.html'
    input_type = 'email'


class URLInput(TextInput):
    template_name = 'floppyforms/url.html'
    input_type = 'url'


class ColorInput(Input):
    template_name = 'floppyforms/color.html'
    input_type = 'color'


class NumberInput(TextInput):
    template_name = 'floppyforms/number.html'
    input_type = 'number'
    min = None
    max = None
    step = None

    def __init__(self, attrs=None):
        default_attrs = {'min': self.min, 'max': self.max, 'step': self.step}
        if attrs:
            default_attrs.update(attrs)
        # Popping attrs if they're not set
        for key in list(default_attrs.keys()):
            if default_attrs[key] is None:
                default_attrs.pop(key)
        super(NumberInput, self).__init__(default_attrs)


class RangeInput(NumberInput):
    template_name = 'floppyforms/range.html'
    input_type = 'range'


class PhoneNumberInput(Input):
    template_name = 'floppyforms/phonenumber.html'
    input_type = 'tel'


def boolean_check(v):
    return not (v is False or v is None or v == '')


class CheckboxInput(Input, forms.CheckboxInput):
    template_name = 'floppyforms/checkbox.html'
    input_type = 'checkbox'

    def __init__(self, attrs=None, check_test=None):
        super(CheckboxInput, self).__init__(attrs)
        self.check_test = boolean_check if check_test is None else check_test

    def get_context(self, name, value, attrs):
        result = self.check_test(value)
        context = super(CheckboxInput, self).get_context(name, value, attrs)
        if result:
            context['widget']['attrs']['checked'] = 'checked'
        return context

    def format_value(self, value):
        if value in ('', True, False, None):
            value = None
        else:
            value = force_text(value)
        return value

    def value_from_datadict(self, data, files, name):
        return forms.CheckboxInput.value_from_datadict(self, data, files, name)


class Select(Input):
    allow_multiple_selected = False
    template_name = 'floppyforms/select.html'

    def __init__(self, attrs=None, choices=()):
        super(Select, self).__init__(attrs)
        self.choices = list(choices)

    def get_context(self, name, value, attrs=None, choices=()):
        context = super(Select, self).get_context(name, value, attrs)

        if self.allow_multiple_selected:
            context['widget']['attrs']['multiple'] = 'multiple'

        # 'groups' look like this:
        # (
        #   ("Optgroup name", (
        #       (value1, label1),
        #       (value2, label2),
        #   )),
        #   (None, [
        #       (value3, label3),
        #       (value4, label4),
        #   ]),
        # )
        groups = []
        for option_value, option_label in chain(self.choices):
            if isinstance(option_label, (list, tuple)):
                group = []
                for val, lab in option_label:
                    group.append((force_text(val), lab))
                groups.append((option_value, group))
            else:
                option_value = force_text(option_value)
                if groups and groups[-1][0] is None:
                    groups[-1][1].append((option_value, option_label))
                else:
                    groups.append((None, [(option_value, option_label)]))
        context["optgroups"] = groups

        return context

    def format_array_value(self, value):
        if value is None:
            return [None]

        if not hasattr(value, '__iter__') or isinstance(value,
                                                        six.string_types):
            value = [value]

        return value

    def format_value(self, value):
        value = self.format_array_value(value)

        if len(value) == 1 and value[0] is None:
            return []

        return set(force_text(v) for v in self.format_array_value(value))


class NullBooleanSelect(Select):
    def __init__(self, attrs=None):
        choices = (('1', _('Unknown')),
                   ('2', _('Yes')),
                   ('3', _('No')))
        super(NullBooleanSelect, self).__init__(attrs, choices)

    def format_value(self, value):
        value = self.format_array_value(value)
        value = value[0]

        try:
            value = {True: '2', False: '3', '2': '2', '3': '3'}[value]
        except KeyError:
            value = '1'

        return value

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        return {'2': True,
                True: True,
                'True': True,
                '3': False,
                'False': False,
                False: False}.get(value, None)


class SelectMultiple(Select):
    allow_multiple_selected = True

    def format_value(self, value):
        if value is None or (len(value) == 1 and value[0] is None):
            value = []
        return [force_text(v) for v in value]

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MULTIVALUE_DICT_TYPES):
            return data.getlist(name)
        return data.get(name, None)


class RadioSelect(Select):
    template_name = 'floppyforms/radio.html'


class CheckboxSelectMultiple(SelectMultiple):
    template_name = 'floppyforms/checkbox_select.html'


class MultiWidget(TemplateBasedWidget, forms.MultiWidget):
    template_name = 'floppyforms/multiwidget.html'

    # Ignore required attribute in Django >= 1.10 or it will be rendered
    # twice
    def use_required_attribute(self, initial):
        return False

    # Backported from Django 1.7
    @property
    def is_hidden(self):
        return all(w.is_hidden for w in self.widgets)

    if django.VERSION < (1, 11):
        # backport
        def format_value(self, value):
            """
            Return a value as it should appear when rendered in a template.
            """
            if value == '' or value is None:
                return None
            if self.is_localized:
                return formats.localize_input(value)
            return force_text(value)

        def get_context(self, name, value, attrs):
            context = super(MultiWidget, self).get_context(name, value, attrs)
            if self.is_localized:
                for widget in self.widgets:
                    widget.is_localized = self.is_localized
            # value is a list of values, each corresponding to a widget
            # in self.widgets.
            if not isinstance(value, list):
                value = self.decompress(value)

            final_attrs = context['widget']['attrs']
            input_type = final_attrs.pop('type', None)
            id_ = final_attrs.get('id')
            subwidgets = []
            for i, widget in enumerate(self.widgets):
                if input_type is not None:
                    widget.input_type = input_type
                widget_name = '%s_%s' % (name, i)
                try:
                    widget_value = value[i]
                except IndexError:
                    widget_value = None
                if id_:
                    widget_attrs = final_attrs.copy()
                    widget_attrs['id'] = '%s_%s' % (id_, i)
                else:
                    widget_attrs = final_attrs
                subwidgets.append(widget.get_context(widget_name, widget_value, widget_attrs)['widget'])
            context['widget']['subwidgets'] = subwidgets
            return context


class SplitDateTimeWidget(MultiWidget):
    supports_microseconds = False

    def __init__(self, attrs=None, date_format=None, time_format=None):
        widgets = (DateInput(attrs=attrs, format=date_format),
                   TimeInput(attrs=attrs, format=time_format))
        super(SplitDateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            value = to_current_timezone(value)
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]


class SplitHiddenDateTimeWidget(SplitDateTimeWidget):
    def __init__(self, attrs=None, date_format=None, time_format=None):
        super(SplitHiddenDateTimeWidget, self).__init__(attrs, date_format,
                                                        time_format)
        for widget in self.widgets:
            widget.input_type = 'hidden'


class SelectDateWidget(Widget):
    """
    A Widget that splits date input into three <select> boxes.

    This also serves as an example of a Widget that has more than one HTML
    element and hence implements value_from_datadict.
    """
    none_value = (0, '---')
    month_field = '%s_month'
    day_field = '%s_day'
    year_field = '%s_year'
    template_name = 'floppyforms/select_date.html'

    def __init__(self, attrs=None, years=None, required=True):
        super(SelectDateWidget, self).__init__(attrs)

        # years is an optional list/tuple of years to use in the
        # "year" select box.
        self.required = required

        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year, this_year + 10)

    def format_value(self, value):
        if value is None:
            return ''

        return value

    def get_context(self, name, value, attrs=None):
        context = super(SelectDateWidget, self).get_context(name, value, attrs)
        context.update({
            'year_field': self.year_field % name,
            'month_field': self.month_field % name,
            'day_field': self.day_field % name
        })

        widget_attrs = context['widget']['attrs']

        # for things like "checked", set the value to False so that the
        # template doesn't render checked="".
        for key, val in attrs.items():
            if val is True:
                widget_attrs[key] = False

        _id = widget_attrs.pop('id')

        context['year_id'] = self.year_field % _id
        context['month_id'] = self.month_field % _id
        context['day_id'] = self.day_field % _id

        year_val, month_val, day_val = self.split_date_values(value)

        context['year_choices'] = [(i, i) for i in self.years]
        context['year_val'] = year_val

        context['month_choices'] = list(MONTHS.items())
        context['month_val'] = month_val

        context['day_choices'] = [(i, i) for i in range(1, 32)]
        context['day_val'] = day_val

        # Theoretically the widget should use self.is_required to determine
        # whether the field is required. For some reason this widget gets a
        # required parameter. The Django behaviour is preferred in this
        # implementation.

        # Django also adds none_value only if there is no value. The choice
        # here is to treat the Django behaviour as a bug: if the value isn't
        # required, then it can be unset.
        if self.required is False:
            context['year_choices'].insert(0, self.none_value)
            context['month_choices'].insert(0, self.none_value)
            context['day_choices'].insert(0, self.none_value)

        return context

    def split_date_values(self, value):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, six.string_types):
                if settings.USE_L10N:
                    try:
                        input_format = formats.get_format(
                            'DATE_INPUT_FORMATS'
                        )[0]
                        v = datetime.datetime.strptime(value, input_format)
                        year_val, month_val, day_val = v.year, v.month, v.day
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = map(int, match.groups())

        return year_val, month_val, day_val

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "0":
            return None
        if y and m and d:
            if settings.USE_L10N:
                input_format = formats.get_format('DATE_INPUT_FORMATS')[0]
                try:
                    date_value = datetime.date(int(y), int(m), int(d))
                except ValueError:
                    return '%s-%s-%s' % (y, m, d)
                else:
                    date_value = datetime_safe.new_date(date_value)
                    return date_value.strftime(input_format)
            else:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)
