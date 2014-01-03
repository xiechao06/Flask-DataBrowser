# -*- coding: utf-8 -*-
from datetime import time
import json
from flask import Markup
import bleach
from flask.ext.babel import gettext
from wtforms import fields, widgets
from flask.ext.databrowser.extra_widgets import (Select2Widget,
                                                 Select2TagsWidget, RichText)


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


SANITIZE_TAGS = ['p', 'br', 'strong', 'em', 'sup', 'sub', 'h3', 'h4', 'h5',
                 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'code']
SANITIZE_ATTRIBUTES = {'a': ['href', 'title', 'target']}


class TinyMceField(fields.TextAreaField):
    """
    Rich text field using TinyMCE.
    """
    widget = RichText()

    def __init__(self, label=u'', validators=None, filters=(),
                 description=u'', id=None, default=None, widget=None,
                 _form=None, _name=None, _prefix='', content_css=None,
                 linkify=True, nofollow=True, tinymce_options=None,
                 sanitize_tags=None, sanitize_attributes=None, **kwargs):

        super(TinyMceField, self).__init__(label=label, validators=validators,
                                           filters=filters,
                                           description=description, id=id,
                                           default=default,
                                           widget=widget, _form=_form,
                                           _name=_name, _prefix=_prefix,
                                           **kwargs)

        if tinymce_options is None:
            tinymce_options = {}
        else:
            # Clone the dict to preserve local edits
            tinymce_options = dict(tinymce_options)

        # Set defaults for TinyMCE
        tinymce_options.setdefault('theme', "advanced")
        tinymce_options.setdefault('plugins', "")
        tinymce_options.setdefault('theme_advanced_buttons1',
                                   ("bold,italic,|,sup,sub,|,bullist,numlist,"
                                    "|,link,unlink,|,blockquote,|"
                                    ",removeformat,code"))
        tinymce_options.setdefault('theme_advanced_buttons2', "")
        tinymce_options.setdefault('theme_advanced_buttons3', "")
        tinymce_options.setdefault('blockformats',
                                   "p,h3,h4,h5,h6,blockquote,dt,dd")
        tinymce_options.setdefault('width', "100%")
        tinymce_options.setdefault('height', "159")
        tinymce_options.setdefault('valid_elements',
                                   ("p,br,strong/b,em/i,sup,sub,h3,h4,h5,h6,"
                                    "ul,ol,li,a[!href|title|target],"
                                    "blockquote,code"))
        tinymce_options.setdefault('theme_advanced_toolbar_location', "top")
        tinymce_options.setdefault('theme_advanced_toolbar_align', "left")
        tinymce_options.setdefault('theme_advanced_statusbar_location',
                                   "bottom")
        tinymce_options.setdefault('theme_advanced_resizing', True)
        tinymce_options.setdefault('theme_advanced_path', False)
        tinymce_options.setdefault('relative_urls', False)

        # Remove options that cannot be set by callers
        tinymce_options.pop('content_css', None)
        tinymce_options.pop('script_url', None)
        tinymce_options.pop('setup', None)

        if sanitize_tags is None:
            sanitize_tags = SANITIZE_TAGS
        if sanitize_attributes is None:
            sanitize_attributes = SANITIZE_ATTRIBUTES

        self.linkify = linkify
        self.nofollow = nofollow
        self.tinymce_options = tinymce_options

        self.content_css = content_css
        self.sanitize_tags = sanitize_tags
        self.sanitize_attributes = sanitize_attributes

    def tinymce_options_json(self):
        return [(Markup(json.dumps(k)), Markup(json.dumps(v))) for k, v in
                self.tinymce_options.items()]

    def process_formdata(self, valuelist):
        super(TinyMceField, self).process_formdata(valuelist)
        # Sanitize data
        self.data = bleach.clean(self.data,
                                 tags=self.sanitize_tags,
                                 attributes=self.sanitize_attributes)
        if self.linkify:
            if self.nofollow:
                self.data = bleach.linkify(self.data)
            else:
                self.data = bleach.linkify(self.data, callbacks=[])
