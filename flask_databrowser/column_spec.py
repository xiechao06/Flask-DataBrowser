
IMAGE = 1
LINK = 2
PLAIN_TEXT = 3
TABLE = 4
UNORDERED_LIST = 5

class ColumnSpec(object):

    def __init__(self, col_name, genre=PLAIN_TEXT, doc="", formatter=None, label="", css_class=None):
        self.col_name = col_name
        self.genre = genre
        self.formatter = formatter
        self.doc = doc
        self.label = label or col_name
        self.css_class = css_class

PlainTextColumnSpec = ColumnSpec # alias to ColumnSpec

class ImageColumnSpec(ColumnSpec):

    def __init__(self, col_name, alt="", doc="", formatter=None, label="", css_class=None):
        super(ImageColumnSpec, self).__init__(col_name, genre=IMAGE, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.alt = alt

class LinkColumnSpec(ColumnSpec):
    def __init__(self, col_name, anchor="", doc="", formatter=None, label="", css_class=None):
        super(LinkColumnSpec, self).__init__(col_name, genre=LINK, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.anchor = anchor

class TableColumnSpec(ColumnSpec):

    def __init__(self, col_name, col_specs=[], anchor="", doc="", formatter=None, label="", css_class=None):
        super(TableColumnSpec, self).__init__(col_name, genre=TABLE, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.anchor = anchor
        self.col_specs = col_specs
    
    def __iter__(self):
        return iter(self.col_specs)
