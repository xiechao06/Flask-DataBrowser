# -*- coding: utf-8 -*-
from datetime import time
import furl
from flask.ext.babel import gettext
from wtforms import fields, widgets
import wtforms_components
from flask.ext.databrowser.extra_widgets import Select2Widget, Select2TagsWidget


class TimeField(fields.Field):
    """
        A text field which stores a `datetime.time` object.
        Accepts time string in multiple formats: 20:10, 20:10:00, 10:00 am, 9:30pm, etc.
    """
    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None, formats=None, **kwargs):
        """
            Constructor

            :param label:
                Label
            :param validators:
                Field validators
            :param formats:
                Supported time formats, as a enumerable.
            :param kwargs:
                Any additional parameters
        """
        super(TimeField, self).__init__(label, validators, **kwargs)

        self.formats = formats or ('%H:%M:%S', '%H:%M',
                                   '%I:%M:%S%p', '%I:%M%p',
                                   '%I:%M:%S %p', '%I:%M %p')

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.formats) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)

            for format in self.formats:
                try:
                    timetuple = time.strptime(date_str, format)
                    self.data = time(timetuple.tm_hour, timetuple.tm_min, timetuple.tm_sec)
                    return
                except ValueError:
                    pass

            raise ValueError(gettext('Invalid time format'))


class Select2Field(fields.SelectField):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form.js and select2 stylesheet for it to
        work.
    """
    widget = Select2Widget()


class Select2TagsField(fields.TextField):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text field.
    You must include select2.js, form.js and select2 stylesheet for it to work.
    """
    widget = Select2TagsWidget()

    def __init__(self, label=None, validators=None, save_as_list=False, **kwargs):
        """Initialization

        :param save_as_list:
            If `True` then populate ``obj`` using list else string
        """
        self.save_as_list = save_as_list
        super(Select2TagsField, self).__init__(label, validators, **kwargs)

    def process_formdata(self, valuelist):
        if self.save_as_list:
            self.data = [v.strip() for v in valuelist[0].split(',') if v.strip()]
        else:
            self.data = valuelist[0]

    def _value(self):
        return u', '.join(self.data) if isinstance(self.data, list) else self.data


class URLField(fields.html5.URLField):
    '''
    why bother to write our own URLField, because sqlalchemy-utils will
    convert the field value to furl
    '''
    def process_formdata(self, valuelist):
        """
        Process data received over the wire from a form.

        This will be called during form construction with data supplied
        through the `formdata` argument.

        :param valuelist: A list of strings to process.
        """
        if valuelist:
            self.data = furl.furl(valuelist[0])
        else:
            self.data = furl.furl('')


class ChoiceSelectField(wtforms_components.SelectField):
    '''
    why provides this field for ChoiceType, because only when
    wtforms_components.SelectField requires when field's data is the choice's code,
    the choice is selected
    '''
    def process_data(self, value):
        self.data = value.code
