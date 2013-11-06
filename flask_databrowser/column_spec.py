IMAGE = 1
LINK = 2
PLAIN_TEXT = 3
TABLE = 4
UNORDERED_LIST = 5
INPUT = 6   # this is a special column type, the actual input type is determined
# by the column's type
PLACE_HOLDER = 7
SELECT = 8
FILE = 9


class ColumnSpec(object):
    def __init__(self, col_name, genre=PLAIN_TEXT, doc=None, formatter=None, label=None, css_class="control-text",
                 trunc=None, form_width_class=None):
        self.col_name = col_name
        self.genre = genre
        self.formatter = formatter
        self.doc = doc
        self.label = label
        self.css_class = css_class
        self.trunc = trunc
        self.form_width_class = form_width_class


PlainTextColumnSpec = ColumnSpec # alias to ColumnSpec


class ImageColumnSpec(ColumnSpec):
    def __init__(self, col_name, alt="", doc=None, formatter=None, label=None, css_class=None):
        super(ImageColumnSpec, self).__init__(col_name, genre=IMAGE, doc=doc, formatter=formatter, label=label,
                                              css_class=css_class)
        self.alt = alt


class LinkColumnSpec(ColumnSpec):
    def __init__(self, col_name, anchor="", doc=None, formatter=None, label=None, css_class="control-text"):
        super(LinkColumnSpec, self).__init__(col_name, genre=LINK, doc=doc, formatter=formatter, label=label,
                                             css_class=css_class)
        self.anchor = anchor


class TableColumnSpec(ColumnSpec):
    def __init__(self, col_name, col_specs=[], anchor="", doc=None, formatter=None, label=None,
                 css_class="table table-condensed table-bordered",
                 sum_fields=[], preprocess=None):
        """
        :param col_name: the col_name of the object must return an iterable, and each item must be of 'db.Model'
        """
        super(TableColumnSpec, self).__init__(col_name, genre=TABLE, doc=doc, formatter=formatter, label=label,
                                              css_class=css_class)
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
                 doc=None,
                 formatter=None,
                 label=None,
                 css_class="",
                 filter_=None, # a function to add filters to query
                 opt_filter=None, # a function to filter options
                 validators=None, # user provided validators
                 property_=None, # corresponding to column definition in model,
                 form_width_class=None):
        super(InputColumnSpec, self).__init__(col_name, genre=INPUT, doc=doc, formatter=formatter, label=label,
                                              css_class=css_class, form_width_class=form_width_class)
        self.group_by = group_by
        self.read_only = read_only
        self.filter_ = filter_ or (lambda v: v)
        self.opt_filter = opt_filter or (lambda obj: True)
        self.validators = validators or []
        self.property_ = property_

    @property
    def grouper_input_name(self):
        if hasattr(self.group_by, "property"):
            try:
                return self.col_name + "." + self.group_by.property.mapper.class_.__name__
            except AttributeError:
                return self.col_name + "." + unicode(self.group_by)
        elif hasattr(self.group_by, "__call__"):
            return self.col_name + "." + self.group_by.func_name
        else:
            return self.col_name + "." + unicode(self.group_by)


class ListColumnSpec(ColumnSpec):
    def __init__(self, col_name, item_col_spec=None, doc=None, formatter=None, label=None, css_class="",
                 compressed=False, item_css_class="", form_width_class=None):
        super(ListColumnSpec, self).__init__(col_name, genre=UNORDERED_LIST, doc=doc, formatter=formatter, label=label,
                                             css_class=css_class, form_width_class=form_width_class)
        self.item_col_spec = item_col_spec
        self.compressed = compressed
        self.item_css_class = item_css_class


class PlaceHolderColumnSpec(ColumnSpec):
    def __init__(self, col_name, template_fname, label=None, doc=None, as_input=False, validators=None, filter_=None,
                 form_width_class=None):
        super(PlaceHolderColumnSpec, self).__init__(col_name, genre=PLACE_HOLDER, label=label, doc=doc,
                                                    form_width_class=form_width_class)
        self.template_fname = template_fname
        self.as_input = as_input
        if self.as_input: # fake InputColumnSpec
            self.group_by = None
            self.read_only = False
            self.filter_ = None
            self.validators = validators or []
            self.opt_filter = None
        self.filter_ = filter_ or (lambda q: q)


class SelectColumnSpec(ColumnSpec):
    def __init__(self, col_name, read_only=False, doc=None, formatter=None, label=None, css_class="", validators=None,
                 choices=None):
        super(SelectColumnSpec, self).__init__(col_name, genre=SELECT, doc=doc, formatter=formatter, label=label,
                                               css_class=css_class)
        self.read_only = read_only
        self.validators = validators or []
        self.choices = choices or []


class FileColumnSpec(ColumnSpec):
    def __init__(self, col_name, label, validators=None):
        super(FileColumnSpec, self).__init__(col_name, genre=FILE, label=label)
        self.validators = validators or []