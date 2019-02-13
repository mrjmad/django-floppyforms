import django

from django import forms
from django.template.loader import get_template
from django.utils.encoding import python_2_unicode_compatible

from .compat import get_context


__all__ = ('BaseForm', 'Form',)


@python_2_unicode_compatible
class LayoutFormMixin(object):
    _render_as_template_name = 'floppyforms/_render_as.html'
    _layout_template = None

    def _render_as(self, layout):
        template = get_template(self._render_as_template_name)
        context = get_context({
            'form': self,
            'layout': layout,
        })

        return template.render(context)

    def __str__(self):
        return self._render_as('floppyforms/layouts/default.html')

    def as_p(self):
        return self._render_as('floppyforms/layouts/p.html')

    def as_ul(self):
        return self._render_as('floppyforms/layouts/ul.html')

    def as_table(self):
        return self._render_as('floppyforms/layouts/table.html')


if django.VERSION < (1, 11):
    class BaseForm(LayoutFormMixin, forms.BaseForm):
        pass

    class Form(LayoutFormMixin, forms.Form):
        pass
else:
    from django.forms.renderers import TemplatesSetting

    class BaseForm(LayoutFormMixin, forms.BaseForm):
        def __init__(self, *args, **kwargs):
            super(BaseForm, self).__init__(*args, **kwargs)
            self.renderer = TemplatesSetting()

    class Form(LayoutFormMixin, forms.Form):
        def __init__(self, *args, **kwargs):
            super(Form, self).__init__(*args, **kwargs)
            self.renderer = TemplatesSetting()
