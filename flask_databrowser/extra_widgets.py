# -*- coding: UTF-8 -*-
"""
extra widgets beside wtform's widgets
"""
import operator
import uuid
from wtforms.widgets import HTMLString, html_params, Select
from wtforms.compat import text_type
from flask.ext.databrowser.column_spec import ColumnSpec
from flask.ext.databrowser.utils import get_primary_key


class Image(object):
    def __init__(self, src, alt):
        self.src = src
        self.alt = alt

    # field is used here to compatiple with wtform's widgets
    def __call__(self, field, **kwargs):
        if "class" in kwargs:
            kwargs["class"] = " ".join(["img-responsive", kwargs["class"]])
        else:
            kwargs["class"] = "img-responsive"
        return HTMLString(
            '<a href="%s" class="fancybox control-text" rel="group" title="%s"><img  %s /></a>' % (
                self.src, self.alt, html_params(src=self.src, alt=self.alt, **kwargs)))


class Link(object):
    def __init__(self, anchor, href):
        self.anchor = anchor
        self.href = href

    def __call__(self, field, **kwargs):
        return HTMLString('<a %s>%s</a>' % (html_params(href=self.href, **kwargs), self.anchor))


class PlainText(object):
    def __init__(self, s, trunc):
        self.s = s
        self.trunc = trunc

    def __call__(self, field, **kwargs):
        need_trunc = False
        s = self.s
        if self.trunc:
            if len(self.s) > self.trunc:
                s = self.s[:self.trunc - 3]
                need_trunc = True
        content = []
        for i in xrange(0, len(self.s), 24):
            content.append(self.s[i:i + 24])
        if not need_trunc:
            return HTMLString('<span %s style="display:inline-block">%s</span>' % (html_params(**kwargs), s))
        else:
            return HTMLString(
                '<span style="display:inline-block" data-toggle="tooltip" data-html="true" data-placement="bottom" '
                'title="%s" %s>%s<a href="#" >...</a></span>' % (
                    "\n".join(content), html_params(**kwargs), s))


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
                    html.append(
                        " <li class=\"%s\" >%s</li>\n" % (self.item_css_class, converter(row, self.item_col_spec)()))
            html.append("</%s>" % self.html_tag)
        else:
            uuid_ = uuid.uuid1()
            if self.rows:
                html = ['<div class="panel-group">', '<div class="panel panel-default">',
                        '<div class="panel-heading"><h4 class="panel-title">'
                        '<a href="#" data-target="#%s" data-toggle="collapse">%d<i '
                        'class="fa fa-chevron-up fa-fw"></i></a></h4></div>' % (
                            uuid_, len(self.rows)),
                        '<div id="%s" class="panel-collapse collapse" data-builtin="true">\n<div class="panel-body">' % uuid_]
                if self.rows:
                    html.append("<ul class='nav nav-pills nav-stacked'>")
                for row in self.rows:
                    converter = ValueConverter(row, self.model_view)
                    html.append(" <li>%s</li>\n" % converter(row, self.item_col_spec)())
                html.append('</div>\n</div>\n<div>\n</div>')
            else:
                html = ["0"]
        return HTMLString(''.join(html))


class PlaceHolder(object):
    def __init__(self, template_fname, field_value, obj, model_view, options):
        self.template_fname = template_fname
        self.obj = obj
        self.field_value = field_value
        self.kwargs = {}
        self.model_view = model_view
        self.options = options

    def set_args(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, field, **kwargs):
        from flask import render_template

        return render_template(self.template_fname,
                               field_value=self.field_value,
                               obj=self.obj,
                               model_view=self.model_view,
                               options=self.options,
                               **self.kwargs)


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


if __name__ == "__main__":
    print Image("http://a.com/a.jpg", "an image")(None)
    print Link("a.com", "http://a.com")(None)
    print PlainText("abc<123")(None)
    from collections import namedtuple
    from flask.ext.databrowser.column_spec import LinkColumnSpec, ImageColumnSpec, ColumnSpec

    table_column_spec = [LinkColumnSpec("a", "some link"), ImageColumnSpec("b"), ColumnSpec("c")]
    print TableWidget([namedtuple("A", ["a", "b", "c"])(i, i * 2, i * 3) for i in xrange(10)], ["a", "b", "c"])(None)

