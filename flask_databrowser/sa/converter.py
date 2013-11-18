#import pytz
from collections import OrderedDict
from decimal import Decimal

from wtforms import (BooleanField, FloatField, TextAreaField, PasswordField)
from wtforms.widgets import (CheckboxInput, TextArea)
from wtforms.validators import (Length, NumberRange)
import sqlalchemy as sa
from sqlalchemy_utils import types
from wtforms_components import (ColorField, DateField, DateRange,
                                DateTimeField, DateTimeLocalField,
                                DecimalField, Email, EmailField, IntegerField,
                                NumberRangeField, PhoneNumberField,
                                SelectField, StringField, TimeField, TimeRange,
                                Unique)
from wtforms_components.widgets import (ColorInput, EmailInput, DateInput,
                                        DateTimeInput, DateTimeLocalInput,
                                        NumberInput, TextInput, TimeInput)
from .exc import UnknownTypeException
from .utils import (is_date_column, is_integer_column, null_or_unicode)


class Converter(object):
    """
    Base form generator, you can make your own form generators by inheriting
    this class.
    """

    # When converting SQLAlchemy types to fields this ordered dict is iterated
    # in given order. This allows smart type conversion of different inherited
    # type objects.
    TYPE_MAP = OrderedDict((
        (sa.types.UnicodeText, TextAreaField),
        (sa.types.BigInteger, IntegerField),
        (sa.types.SmallInteger, IntegerField),
        (sa.types.Text, TextAreaField),
        (sa.types.Boolean, BooleanField),
        (sa.types.Date, DateField),
        (sa.types.DateTime, DateTimeField),
        (sa.types.Enum, SelectField),
        (sa.types.Float, FloatField),
        (sa.types.Integer, IntegerField),
        (sa.types.Numeric, DecimalField),
        (sa.types.String, StringField),
        (sa.types.Time, TimeField),
        (sa.types.Unicode, StringField),
        (types.ArrowType, DateTimeField),
        (types.ChoiceType, SelectField),
        (types.ColorType, ColorField),
        (types.EmailType, EmailField),
        (types.NumberRangeType, NumberRangeField),
        (types.PasswordType, PasswordField),
        (types.PhoneNumberType, PhoneNumberField),
        (types.ScalarListType, StringField),
        (types.UUIDType, StringField),
    ))

    WIDGET_MAP = OrderedDict((
        (BooleanField, CheckboxInput),
        (ColorField, ColorInput),
        (DateField, DateInput),
        (DateTimeField, DateTimeInput),
        (DateTimeLocalField, DateTimeLocalInput),
        (DecimalField, NumberInput),
        (EmailField, EmailInput),
        (FloatField, NumberInput),
        (IntegerField, NumberInput),
        (TextAreaField, TextArea),
        (TimeField, TimeInput),
        (StringField, TextInput)
    ))

    def create_field(self, column, **kwargs):
        """
        Create form field for given column.

        :param column: SQLAlchemy Column object.
        """
        kwargs = {}
        field_class = self.get_field_class(column)
        kwargs.update(self.type_specific_parameters(column))
        kwargs.update('validators', self.create_validators(column))
        if issubclass(field_class, DecimalField):
            if hasattr(column.type, 'scale'):
                kwargs['places'] = column.type.scale
        field = field_class(**kwargs)
        return field

    def get_field_class(self, column):
        """
        Returns WTForms field class. Class is based on a custom field class
        attribute or SQLAlchemy column type.

        :param column: SQLAlchemy Column object
        """
        if 'choices' in column.info and column.info['choices']:
            return SelectField
        if (type(column.type) not in self.TYPE_MAP) and \
           isinstance(column.type, sa.types.TypeDecorator):
            check_type = column.type.impl
        else:
            check_type = column.type
        for type_ in self.TYPE_MAP:
            if isinstance(check_type, type_):
                return self.TYPE_MAP[type_]
        raise UnknownTypeException(column)

    def date_format(self, column):
        """
        Returns date format for given column.

        :param column: SQLAlchemy Column object
        """
        if (
            isinstance(column.type, sa.types.DateTime) or
            isinstance(column.type, types.ArrowType)
        ):
            return self.meta.datetime_format

        if isinstance(column.type, sa.types.Date):
            return self.meta.date_format

    def type_specific_parameters(self, column):
        """
        Returns type specific parameters for given column.

        :param column: SQLAlchemy Column object
        """
        kwargs = {}
        if (
            hasattr(column.type, 'enums') or
            column.info.get('choices') or
            isinstance(column.type, types.ChoiceType)
        ):
            kwargs.update(self.select_field_kwargs(column))

        date_format = self.date_format(column)
        if date_format:
            kwargs['format'] = date_format

        if hasattr(column.type, 'country_code'):
            kwargs['country_code'] = column.type.country_code

        kwargs['widget'] = self.widget(column)
        return kwargs

    def widget(self, column):
        """
        Returns WTForms widget for given column.

        :param column: SQLAlchemy Column object
        """
        widget = column.info.get('widget', None)
        if widget is not None:
            return widget

        kwargs = {}

        step = column.info.get('step', None)
        if step is not None:
            kwargs['step'] = step
        else:
            if isinstance(column.type, sa.types.Numeric):
                if (
                    column.type.scale is not None and
                    not column.info.get('choices')
                ):
                    kwargs['step'] = self.scale_to_step(column.type.scale)

        if kwargs:
            widget_class = self.WIDGET_MAP[
                self.get_field_class(column)
            ]
            return widget_class(**kwargs)

    def scale_to_step(self, scale):
        """
        Returns HTML5 compatible step attribute for given decimal scale.

        :param scale: an integer that defines a Numeric column's scale
        """
        return str(pow(Decimal('0.1'), scale))

    def select_field_kwargs(self, column):
        """
        Returns key value args for SelectField based on SQLAlchemy column
        definitions.

        :param column: SQLAlchemy Column object
        """
        kwargs = {}
        kwargs['coerce'] = self.coerce(column)
        if isinstance(column.type, types.ChoiceType):
            kwargs['choices'] = column.type.choices
        elif 'choices' in column.info and column.info['choices']:
            kwargs['choices'] = column.info['choices']
        else:
            kwargs['choices'] = [
                (enum, enum) for enum in column.type.enums
            ]
        return kwargs

    def coerce(self, column):
        """
        Returns coerce callable for given column

        :param column: SQLAlchemy Column object
        """
        try:
            python_type = column.type.python_type
        except NotImplementedError:
            return null_or_unicode

        if column.nullable and issubclass(python_type, basestring):
            return null_or_unicode
        return python_type

    def create_validators(self, column):
        """
        Returns validators for given column

        :param column: SQLAlchemy Column object
        """
        validators = [
            self.length_validator(column),
            self.unique_validator(column),
            self.range_validator(column)
        ]
        validators = [v for v in validators if v is not None]
        if isinstance(column.type, types.EmailType):
            validators.append(Email())
        return validators

    def unique_validator(self, column):
        """
        Returns unique validator for given column if column has a unique index

        :param column: SQLAlchemy Column object
        """
        if column.unique:
            return Unique(
                getattr(self.model_class, column.key),
                get_session=self.form_class.get_session
            )

    def range_validator(self, column):
        """
        Returns range validator based on column type and column info min and
        max arguments

        :param column: SQLAlchemy Column object
        """
        min_ = column.info.get('min', None)
        max_ = column.info.get('max', None)

        if min_ is not None or max_ is not None:
            if is_integer_column(column):
                return NumberRange(min=min_, max=max_)
            elif is_date_column(column):
                return DateRange(min=min_, max=max_)
            elif isinstance(column.type, sa.types.Time):
                return TimeRange(min=min_, max=max_)

    def length_validator(self, column):
        """
        Returns length validator for given column

        :param column: SQLAlchemy Column object
        """
        if isinstance(column.type, sa.types.String) and \
           hasattr(column.type, 'length') and column.type.length:
            return Length(max=column.type.length)
