# -*- coding: UTF-8 -*-
"""
extra widgets beside wtform's widgets
"""
import operator
import uuid
from wtforms.widgets import HTMLString, html_params
from wtforms.compat import text_type, string_types, iteritems
from flask.ext.databrowser.column_spec import ColumnSpec
from flask.ext.sqlalchemy import Model
from flask.ext.databrowser.utils import get_primary_key

class Image(object):
    def __init__(self, src, alt):
        self.src = src
        self.alt = alt

    # field is used here to compatiple with wtform's widgets
    def __call__(self, field, **kwargs):
        return HTMLString(
            '<a href="%s" class="fancybox control-text" rel="group" title="%s"><img '
            '%s /></a>' % (
            self.src, self.alt,
            html_params(src=self.src, alt=self.alt, **kwargs)))

class Link(object):

    def __init__(self, anchor, href):
        self.anchor = anchor
        self.href = href

    def __call__(self, field, **kwargs):
        return HTMLString('<a %s>%s</a>' % (html_params(href=self.href, **kwargs), self.anchor))

class PlainText(object):

    def __init__(self, s):
        self.s = s
    
    def __call__(self, field, **kwargs):

        return HTMLString('<span %s>%s</span>' % (html_params(**kwargs), self.s))

class TableWidget(object):

    def __init__(self, rows, model_view, col_specs=None, sum_fields=[], preprocess=None):
        self.rows = rows
        self.model_view = model_view
        self.col_specs = col_specs
        self.sum_fields = sum_fields
        if self.sum_fields:
            self.sum_row = {}
        self.preprocess = preprocess or (lambda v: v)

    def __call__(self, field, **kwargs):
        from flask.ext.databrowser.convert import ValueConverter
        html = ['<table %s>\n' % html_params(**kwargs)]
        if self.rows:
            # get the primary key of rows if possible
            pk = str(uuid.uuid1()) # we set pk to a random value at first
            if self.model_view:
                model = self.rows[0].__class__ 
                if hasattr(model, "_sa_class_manager"):
                    pk = get_primary_key(model)
            col_specs = self.col_specs or [ColumnSpec(col) for col in dir(self.rows[0]) if not col.startswith("_")]
            for i in xrange(len(col_specs)):
                if isinstance(col_specs[i], basestring):
                    if col_specs[i] == pk:
                        col_specs[i] = self.model_view.data_browser.create_object_link_column_spec(self.rows[0].__class__, "") or ColumnSpec(col_specs[i])
                    else:
                        col_specs[i] = ColumnSpec(col_specs[i])
            #col_specs = [ColumnSpec(col) if isinstance(col, basestring) else col for col in col_specs]
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
                for sub_col_spec in col_specs:
                    converter = ValueConverter(row, self.model_view)
                    s += "    <td>%s</td>\n" % converter(operator.attrgetter(sub_col_spec.col_name)(preprocessed_row), sub_col_spec)()
                    if sub_col_spec.col_name in self.sum_fields:
                        try:
                            self.sum_row[sub_col_spec.col_name] += operator.attrgetter(sub_col_spec.col_name)(preprocessed_row)
                        except KeyError:
                            self.sum_row[sub_col_spec.col_name] = operator.attrgetter(sub_col_spec.col_name)(preprocessed_row)
                s += "  </tr>\n"
                html.append(s)
            if self.sum_fields:
                s = "  <tr>\n"
                s += u"    <td>总计</td>\n"
                for sub_col_spec in col_specs:
                    if sub_col_spec.col_name in self.sum_fields:
                        s += "    <td>%s</td>" % converter(self.sum_row.get(sub_col_spec.col_name), sub_col_spec)()
                    else:
                        s += "    <td></td>"
                s += "  </tr>\n"
                html.append(s)
        html.append('</table>')
        return HTMLString(''.join(html))

class ListWidget(object):

    def __init__(self, rows, item_col_spec, html_tag="ul", model_view=None, compressed=False):
        self.rows = rows
        self.item_col_spec = item_col_spec
        self.html_tag = html_tag
        self.model_view = model_view
        self.compressed = compressed

    def __call__(self, field, **kwargs):
        from flask.ext.databrowser.convert import ValueConverter

        if not self.compressed:
            html = ["<%s>\n" % self.html_tag]
            for row in self.rows:
                converter = ValueConverter(row, self.model_view)
                html.append(" <li>%s</li>\n" % converter(row, self.item_col_spec)())
            html.append("</%s>" % self.html_tag)
        else:
            uuid_ = uuid.uuid1()
            if self.rows:
                html = ['<a href="#" data-target="#%s" data-toggle="collapse">%d</a>' % (uuid_, len(self.rows))]
                html.append('<i class="icon-chevron-down"></i>')
                html.append('<div id="%s" class="collapse in" data-builtin="true">\n<div class="accordion-inner">' % uuid_)
                for row in self.rows:
                    converter = ValueConverter(row, self.model_view)
                    html.append(" <div>%s</div>\n" % converter(row, self.item_col_spec)())
                html.append('</div>\n</div>')
            else:
                html = ["0"]
        return HTMLString(''.join(html))

class PlaceHolder(object):
    def __init__(self, template_fname, field_value, obj, model_view):
        self.template_fname = template_fname
        self.obj = obj
        self.field_value = field_value
        self.kwargs = {}
        self.model_view = model_view

    def set_args(self, **kwargs):
        self.kwargs = kwargs
    
    def __call__(self, field, **kwargs):
        from flask import render_template
        return render_template(self.template_fname, 
                               field_value=self.field_value, 
                               obj=self.obj, 
                               model_view=self.model_view,
                               **self.kwargs)

if __name__ == "__main__":
    print Image("http://a.com/a.jpg", "an image")(None)
    print Link("a.com", "http://a.com")(None)
    print PlainText("abc<123")(None)
    from collections import namedtuple
    from flask.ext.databrowser.column_spec import LinkColumnSpec, ImageColumnSpec, ColumnSpec
    table_column_spec = [LinkColumnSpec("a", "some link"), ImageColumnSpec("b"), ColumnSpec("c")]
    print TableWidget([namedtuple("A", ["a", "b", "c"])(i, i*2, i*3) for i in xrange(10)], ["a", "b", "c"])(None)
