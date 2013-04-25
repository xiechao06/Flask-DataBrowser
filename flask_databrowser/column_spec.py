
IMAGE = 1
LINK = 2
PLAIN_TEXT = 3
TABLE = 4
UNORDERED_LIST = 5
INPUT = 6   # this is a special column type, the actual input type is determined
            # by the column's type
PLACE_HOLDER = 7


class ColumnSpec(object):

    def __init__(self, col_name, genre=PLAIN_TEXT, doc="", formatter=None, label=None, css_class="control-text"):
        self.col_name = col_name
        self.genre = genre
        self.formatter = formatter
        self.doc = doc
        self.label = col_name if (label is None) else label
        self.css_class = css_class

PlainTextColumnSpec = ColumnSpec # alias to ColumnSpec

class ImageColumnSpec(ColumnSpec):

    def __init__(self, col_name, alt="", doc="", formatter=None, label="", css_class=None):
        super(ImageColumnSpec, self).__init__(col_name, genre=IMAGE, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.alt = alt

class LinkColumnSpec(ColumnSpec):
    def __init__(self, col_name, anchor="", doc="", formatter=None, label="", css_class="control-text"):
        super(LinkColumnSpec, self).__init__(col_name, genre=LINK, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.anchor = anchor

class TableColumnSpec(ColumnSpec):

    def __init__(self, col_name, col_specs=[], anchor="", doc="", formatter=None, label="", css_class="table table-condensed table-bordered", 
        sum_fields=[], preprocess=None):
        """
        :param col_name: the col_name of the object must return an iterable, and each item must be of 'db.Model'
        """
        super(TableColumnSpec, self).__init__(col_name, genre=TABLE, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.anchor = anchor
        self.col_specs = col_specs
        self.sum_fields = sum_fields
        self.preprocess = preprocess
    
    def __iter__(self):
        return iter(self.col_specs)

class InputColumnSpec(ColumnSpec):

    def __init__(self, col_name, 
                 group_by=None, # a grouper field, must be of `InstrumentedAttribute`
                 read_only=False, 
                 doc="", 
                 formatter=None, 
                 label="", 
                 css_class="", 
                 filter_=None, # a function to add filters to query 
                 opt_filter=None, # a function to filter options
                 validators=None, # user provided validators
                ):
        super(InputColumnSpec, self).__init__(col_name, genre=INPUT, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.group_by = group_by
        self.read_only = read_only
        self.filter_ = filter_ or (lambda v: v)
        self.opt_filter = opt_filter or (lambda obj: True)
        self.validators = validators or []
    
    @property
    def grouper_input_name(self):
        return self.col_name + '.' +  self.group_by.property.mapper.class_.__name__

class ListColumnSpec(ColumnSpec):

    def __init__(self, col_name, item_col_spec=None, doc="", formatter=None, label="", css_class="", compressed=False):
        super(ListColumnSpec, self).__init__(col_name, genre=UNORDERED_LIST, doc=doc, formatter=formatter, label=label, css_class=css_class)
        self.item_col_spec = item_col_spec
        self.compressed = compressed

class PlaceHolderColumnSpec(ColumnSpec):

    def __init__(self, col_name, label, template_fname):
        super(PlaceHolderColumnSpec, self).__init__(col_name, genre=PLACE_HOLDER, label=label)
        self.template_fname = template_fname
