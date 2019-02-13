import os.path

import django
import warnings

warnings.simplefilter('always')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'floppyforms.sqlite',
    },
}

USE_I18N = True
USE_L10N = True

INSTALLED_APPS = [
    'django.contrib.gis',
    'floppyforms',
    'tests',
]

MIDDLEWARE_CLASSES = ()

STATIC_URL = '/static/'

SECRET_KEY = '0'

template_options = {
    'context_processors': [
        # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
        # list if you haven't customized them:
        'django.template.context_processors.debug',
        'django.template.context_processors.i18n',
        'django.template.context_processors.media',
        'django.template.context_processors.static',
        'django.template.context_processors.tz',
    ]
}

if django.VERSION >= (1, 9):
    template_options['builtins'] = [
        'django.templatetags.i18n',
        'django.templatetags.static',
        'django.templatetags.tz',
    ]

if django.VERSION < (1, 11):
    template_directories = []
else:
    template_directories = [
        os.path.join(
            os.path.dirname(django.__file__),
            "forms/templates/"
        )
    ]
    

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': template_directories,
        'APP_DIRS': True,
        'OPTIONS': template_options,
    },
]

if django.VERSION < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'
