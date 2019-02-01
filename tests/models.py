from django import VERSION as DJANGO_VERSION
from django.core.validators import validate_comma_separated_integer_list

from django.db import models


class Registration(models.Model):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    age = models.IntegerField()


class AllFields(models.Model):
    boolean = models.BooleanField(default=False)
    char = models.CharField(max_length=50)

    if DJANGO_VERSION < (1, 11):
        comma_separated = models.CommaSeparatedIntegerField(max_length=50)
    else:
        comma_separated = models.CharField(
            max_length=50,
            validators=[validate_comma_separated_integer_list])

    date = models.DateField()
    datetime = models.DateTimeField()
    decimal = models.DecimalField(decimal_places=2, max_digits=4)
    email = models.EmailField()
    file_path = models.FilePathField()
    float_field = models.FloatField()
    integer = models.IntegerField()
    big_integer = models.BigIntegerField()

    if DJANGO_VERSION < (1, 9):
        ip_address = models.IPAddressField()

    generic_ip_address = models.GenericIPAddressField()
    null_boolean = models.NullBooleanField()
    positive_integer = models.PositiveIntegerField()
    positive_small_integer = models.PositiveSmallIntegerField()
    slug = models.SlugField()
    small_integer = models.SmallIntegerField()
    text = models.TextField()
    time = models.TimeField()
    url = models.URLField()
    file_field = models.FileField(upload_to="test/")
    image = models.ImageField(upload_to="test/")
    fk = models.ForeignKey(Registration, related_name='all_fk', on_delete=models.CASCADE)
    m2m = models.ManyToManyField(Registration, related_name='all_m2m')
    one = models.OneToOneField(Registration, related_name='all_one', on_delete=models.CASCADE)
    choices = models.CharField(max_length=50, choices=(('a', 'a'),))


class ImageFieldModel(models.Model):
    image_field = models.ImageField(upload_to='_test_uploads', null=True,
                                    blank=True)
