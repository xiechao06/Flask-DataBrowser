"""
extra widgets beside wtform's widgets
"""
import operator
from wtforms.widgets import HTMLString, html_params
from wtforms.compat import text_type, string_types, iteritems
from flask.ext.databrowser.column_spec import ColumnSpec

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

    def __init__(self, rows, col_spec=None):
        self.rows = rows
        self.col_spec = col_spec
        from flask.ext.databrowser.convert import ValueConverter
        self.converter = ValueConverter()

    def __call__(self, field, **kwargs):
        
        html = ['<table %s>\n' % html_params(**kwargs)]
        if self.rows:
            column_specs = []
            if self.col_spec:
                column_spec = self.col_spec.col_specs
            if not column_specs:
                column_specs = list(ColumnSpec(col_name) for col_name in self.rows[0].__dict__.keys())
            html.append('  <tr>\n%s\n  </tr>\n' % "\n".join(text_type(col.col_name).join(["    <th>", "</th>"]) for col in column_specs))
            # data rows
            for row in self.rows:
                s = "  <tr>\n"
                for sub_col_spec in column_specs:
                    s += "    <td>%s</td>\n" % self.converter(operator.attrgetter(sub_col_spec.col_name)(row), sub_col_spec)()
                s += "  </tr>\n"
                html.append(s)
        html.append('</table>')
        return HTMLString(''.join(html))

class ListWidget(object):

    def __init__(self, rows, col_spec, html_tag="ul"):
        self.rows = rows
        self.col_spec = col_spec
        self.html_tag = html_tag
        from flask.ext.databrowser.convert import ValueConverter
        self.converter = ValueConverter()

    def __call__(self, field, **kwargs):

        html = ["<%s>\n" % self.html_tag]
        for row in self.rows:
            html.append(" <li>%s</li>\n" % self.converter(row, self.col_spec)())
        html.append("</%s>" % self.html_tag)
        return HTMLString(''.join(html))

if __name__ == "__main__":
    print Image("http://a.com/a.jpg", "an image")(None)
    print Link("a.com", "http://a.com")(None)
    print PlainText("abc<123")(None)
    from collections import namedtuple
    from flask.ext.databrowser.column_spec import LinkColumnSpec, ImageColumnSpec, ColumnSpec
    table_column_spec = [LinkColumnSpec("a", "some link"), ImageColumnSpec("b"), ColumnSpec("c")]
    print TableWidget([namedtuple("A", ["a", "b", "c"])(i, i*2, i*3) for i in xrange(10)])(None)
    print ListWidget([1, 2, 3], LinkColumnSpec(""))(None)
