# -*- coding: UTF-8 -*-
"""
extra widgets beside wtform's widgets
"""
import urllib
import urlparse
import operator
import datetime

from flask import render_template, _request_ctx_stack
import uuid
import time
from flask.ext.babel import gettext, ngettext
from wtforms import fields, widgets
from wtforms.widgets import (HTMLString, html_params, Select, TextInput)
from wtforms.compat import text_type
from flask.ext.databrowser.sa.sa_utils import get_primary_key
from flask.ext.databrowser.utils import random_str
#from flask.ext.databrowser.column_spec import ColumnSpec


class Image(object):

    SMALL = 1
    NORMAL = 2
    LARGE = 3

    def __init__(self, size_type=NORMAL):
        self.size_type = size_type

    # field is used here to compatiple with wtform's widgets
    def __call__(self, field, **kwargs):
        # TODO use a more advanced library, such as:
        # http://brutaldesign.github.io/swipebox
        if "class" in kwargs:
            kwargs["class"] = " ".join(["img-responsive", kwargs["class"]])
        else:
            kwargs["class"] = "img-responsive"
        # TODO shrink using class, and proportinalize
        if self.size_type == Image.SMALL:
            kwargs['style'] = 'width: 128px; height: 128px'
        elif self.size_type == Image.NORMAL:
            kwargs['style'] = 'width: 256px; height: 256px'
        html = ('<a href="%s" class="fancybox control-text" rel="group"'
                'title="%s"><img  %s /></a>')

        # why do this? force browser to refresh the images
        value = field._value()
        if isinstance(value, basestring):
            value = [value]
        htmls = []
        for url in value:
            params = {'random': random_str()}
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.urlencode(query)
            url = urlparse.urlunparse(url_parts)

            htmls.append(HTMLString(html % (url, field.label.text,
                                           html_params(src=url,
                                                       alt=field.label.text,
                                                       **kwargs))))
        return ''.join(htmls)

#class Link(object):
    #def __init__(self, anchor, href):
        #self.anchor = anchor
        #self.href = href

    #def __call__(self, field, **kwargs):
        #return HTMLString('<a %s>%s</a>' % (html_params(href=self.href, **kwargs), self.anchor))

class Link(object):

    def __init__(self, target=''):
        self.target = target

    def __call__(self, field, **kwargs):
        anchor, href = field._value()
        return HTMLString('<a %s>%s</a>' %
                          (html_params(href=href, target=self.target, **kwargs), anchor))

class PlainText(object):
    def __init__(self, max_len=None,
                 template='/data_browser__/snippets/plain-text.html',
                 placeholder=' -- '):
        self.max_len = max_len
        self.template = template
        self.placeholder = placeholder

    def __call__(self, field, **kwargs):
        # TODO just hand code
        abbrev = None
        if self.max_len:
            if field._value() and len(field._value()) > self.max_len:
                abbrev = field._value()[:self.max_len - 3]
        v = field._value()
        if v is None:
            v = self.placeholder
        return render_template(self.template, value=v,
                               abbrev=abbrev,
                               html_params=html_params(**kwargs))


class TableWidget(object):
    def __init__(self, rows, model_view, col_specs=None, sum_fields=None, preprocess=None):
        self.rows = rows
        self.model_view = model_view
        self.col_specs = col_specs
        self.sum_fields = sum_fields
        if self.sum_fields:
            self.sum_row = {}
        self.preprocess = preprocess or (lambda v: v)

    def __call__(self, field, **kwargs):
        from flask.ext.databrowser.convert import ValueConverter

        if self.rows:
            html = ['<table %s>\n' % html_params(**kwargs)]
            # get the primary key of rows if possible
            pk = None
            if self.model_view:
                model = self.rows[0].__class__
                if hasattr(model, "_sa_class_manager"):
                    pk = get_primary_key(model)
            if not self.col_specs:
                model = self.rows[0].__class__
                if hasattr(model, '_sa_class_manager'):
                    col_specs = [ColumnSpec(col, label=col) for col in model.__mapper__.iterate_properties]
                else:
                    col_specs = self.col_specs or [ColumnSpec(col, label=col) for col in model.__dict__ if
                                                   not col.startswith("_")]
            else:
                col_specs = self.col_specs

            for i in xrange(len(col_specs)):
                if isinstance(col_specs[i], basestring):
                    if col_specs[i] == pk:
                        col_specs[i] = self.model_view.data_browser.get_object_link_column_spec(
                            self.rows[0].__class__, pk) or ColumnSpec(col_specs[i], label=pk)
                    else:
                        col_specs[i] = ColumnSpec(col_specs[i], label=col_specs[i])
                        #col_specs = [ColumnSpec(col) if isinstance(col, basestring) else col for col in col_specs]
                if isinstance(col_specs[i], ColumnSpec):
                    if col_specs[i].col_name == pk:
                        temp = self.model_view.data_browser.get_object_link_column_spec(self.rows[0].__class__, pk)
                        if temp:
                            col_specs[i] = temp

            html.append('  <thead>\n')
            if self.sum_fields:
                html.append("    <th></th>")
            html.extend("    <th>%s</th>\n" % text_type(col.label) for col in col_specs)
            html.append('  </thead>\n')
            # data rows
            for row in self.rows:
                preprocessed_row = self.preprocess(row)
                s = "  <tr>\n"
                if self.sum_fields:
                    s += "    <td></td>\n"
                converter = ValueConverter(row, self.model_view)
                for sub_col_spec in col_specs:
                    s += "    <td>%s</td>\n" % converter(operator.attrgetter(sub_col_spec.col_name)(preprocessed_row),
                                                         sub_col_spec)()
                    if sub_col_spec.col_name in self.sum_fields:
                        try:
                            self.sum_row[sub_col_spec.col_name] += operator.attrgetter(sub_col_spec.col_name)(
                                preprocessed_row)
                        except KeyError:
                            self.sum_row[sub_col_spec.col_name] = operator.attrgetter(sub_col_spec.col_name)(
                                preprocessed_row)
                s += "  </tr>\n"
                html.append(s)
            if self.sum_fields:
                s = "  <tr>\n"
                s += u"    <td>总计</td>\n"
                converter = ValueConverter(self.sum_row, self.model_view)
                for sub_col_spec in col_specs:
                    if sub_col_spec.col_name in self.sum_fields:
                        s += "    <td>%s</td>" % converter(self.sum_row.get(sub_col_spec.col_name), sub_col_spec)()
                    else:
                        s += "    <td></td>"
                s += "  </tr>\n"
                html.append(s)
            html.append('</table>')
        else:
            html = u"<span class='text-error'>无</span>"
        return HTMLString(''.join(html))


class ListWidget(object):
    def __init__(self, rows, item_col_spec, html_tag="ul", model_view=None, compressed=False, item_css_class=""):
        self.rows = rows
        self.item_col_spec = item_col_spec
        self.html_tag = html_tag
        self.model_view = model_view
        self.compressed = compressed
        self.item_css_class = item_css_class

    def __call__(self, field, **kwargs):
        from flask.ext.databrowser.convert import ValueConverter

        if not self.compressed:
            html = ["<%s %s>\n" % (self.html_tag, html_params(**kwargs))]
            if self.rows:
                for row in self.rows:
                    converter = ValueConverter(row, self.model_view)
                    val = converter(row, self.item_col_spec)
                    if isinstance(getattr(val, "widget", None), Link):
                        html.append(val(**{"class": self.item_css_class}))
                    else:
                        html.append(" <li class=\"%s\" >%s</li>\n" % (self.item_css_class, val()))
            html.append("</%s>" % self.html_tag)
        else:
            uuid_ = uuid.uuid1()
            if self.rows:
                html = ['<div class="panel-group">', '<div class="panel panel-default">',
                        '<div class="panel-heading"><h4 class="panel-title">'
                        '<a href="#" data-target="#%s" data-toggle="collapse">%d<i '
                        'class="fa fa-chevron-up fa-fw"></i></a></h4></div>' % (
                            uuid_, len(self.rows)),
                        '<div id="%s" class="panel-collapse collapse list-group" data-builtin="true">' % uuid_]
                for row in self.rows:
                    converter = ValueConverter(row, self.model_view)
                    html.append(converter(row, self.item_col_spec)(**{"class": "list-group-item"}))
                html.append('</div>\n</div>\n</div>')
            else:
                html = ["0"]
        return HTMLString(''.join(html))


    #class PlaceHolder(object):
    #def __init__(self, template_fname, field_value, obj, model_view, options):
    #self.template_fname = template_fname
    #self.obj = obj
    #self.field_value = field_value
    #self.kwargs = {}
    #self.model_view = model_view
    #self.options = options

    #def set_args(self, **kwargs):
    #self.kwargs = kwargs

    #def __call__(self, field, **kwargs):
    #from flask import render_template

    #return render_template(self.template_fname,
    #field_value=self.field_value,
    #obj=self.obj,
    #model_view=self.model_view,
    #options=self.options,
    #**self.kwargs)


class SelectWidget(Select):
    def __init__(self, field_value, obj, model_view, choices, coerce=text_type, mulitple=False):
        self.choices = choices
        self.field_value = field_value
        self.obj = obj
        self.model_view = model_view
        self.coerce = coerce
        self.multiple = mulitple

    def iter_choices(self):
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == self.field_value)

    def __call__(self, field, **kwargs):
        # kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for val, label, selected in self.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append('</select>')
        return HTMLString(''.join(html))


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
                    self.data = datetime.time(timetuple.tm_hour,
                                              timetuple.tm_min,
                                              timetuple.tm_sec)
                    return
                except ValueError:
                    pass

            raise ValueError(gettext('Invalid time format'))


class Select2Widget(widgets.Select):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form.js and select2 stylesheet for it to
        work.
    """

    def __call__(self, field, **kwargs):
        allow_blank = getattr(field, 'allow_blank', False)

        if allow_blank and not self.multiple:
            kwargs['data-role'] = u'select2blank'
        else:
            kwargs['data-role'] = u'select2'
        if hasattr(field, "iter_optgroups"):
            kwargs.setdefault('id', field.id)
            if self.multiple:
                kwargs['multiple'] = 'multiple'
            html = [u'<select %s>' % html_params(name=field.name, **kwargs)]
            for grouplabel, choices in field.iter_optgroups():
                html.append(self.render_optgroup(grouplabel, choices))
            html.append(u'</select>')
            return HTMLString(u''.join(html))
        else:
            return super(Select2Widget, self).__call__(field, **kwargs)

    @classmethod
    def render_optgroup(cls, grouplabel, choices):
        html = []
        if grouplabel is not None:
            options = {'label': grouplabel}
            html.append(u'<optgroup %s>' % html_params(**options))
        for value, label, selected in choices:
            html.append(cls.render_option(value, label, selected))
        if grouplabel is not None:
            html.append(u'</optgroup>')
        return HTMLString(u''.join(html))


class OptGroupWidget(object):
    def __call__(self, field, **kwargs):
        return Select2Widget.render_optgroup(field.label.text, field.choices)


class DatePickerWidget(TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """

    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datepicker'
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(TextInput):
    """
        Datetime picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """

    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datetimepicker'
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class RenderTemplateWidget(object):
    """
        WTForms widget that renders Jinja2 template
    """

    def __init__(self, template):
        """
            Constructor

            :param template:
                Template path
        """
        self.template = template

    def __call__(self, field, **kwargs):
        ctx = _request_ctx_stack.top
        jinja_env = ctx.app.jinja_env

        kwargs.update({
            'field': field,
            '_gettext': gettext,
            '_ngettext': ngettext,
        })

        template = jinja_env.get_template(self.template)
        return template.render(kwargs)


class Select2TagsWidget(TextInput):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text widget.
    You must include select2.js, form.js and select2 stylesheet for it to work.
    """

    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'select2tags'
        return super(Select2TagsWidget, self).__call__(field, **kwargs)


class PlaceHolder(object):
    def __init__(self, template_fname, field_value, record, **extra_kwargs):
        self.template_fname = template_fname
        self.field_value = field_value
        self.record = record
        self.extra_kwargs = extra_kwargs

    def __call__(self, field, **kwargs):

        if 'query_factory' in kwargs:
            options = kwargs['query_factory'].all()
        else:
            options = None

        return render_template(self.template_fname,
                               field_value=self.field_value, record=self.record, options=options,
                               **self.extra_kwargs)


class HtmlSnippet(object):

    def __init__(self, template, obj, render_kwargs):
        self.template = template
        self.obj = obj
        self.render_kwargs = render_kwargs

    def __call__(self, field, **kwargs):

        if 'query_factory' in kwargs:
            options = kwargs['query_factory'].all()
        else:
            options = None

        return render_template(self.template, field=field,
                               obj=self.obj, options=options,
                               **self.render_kwargs)
