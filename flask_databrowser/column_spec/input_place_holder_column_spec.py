# -*- coding: utf-8 -*-
from .column_spec import (InputColumnSpec, PlaceHolderColumnSpec)


class InputPlaceHolderColumnSpec(InputColumnSpec, PlaceHolderColumnSpec):

    def __init__(self, col_name, template_fname, label=None, doc=None,
                 validators=None, filter_=None, opt_filter=None, kolumne=None):

        InputColumnSpec.__init__(self, col_name=col_name, doc=doc,
                                 label=label, validators=validators,
                                 filter_=filter_, opt_filter=opt_filter,
                                 kolumne=kolumne)
        PlaceHolderColumnSpec.__init__(self, template_fname=template_fname)
