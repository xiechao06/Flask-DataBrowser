# -*- coding: utf-8 -*-
from .column_spec import (InputColumnSpec, PlaceHolderColumnSpec)
from .extra_widgets import PlaceHolder


class InputPlaceHolderColumnSpec(InputColumnSpec, PlaceHolderColumnSpec):

    def __init__(self, col_name, template_fname, label=None, doc=None,
                 validators=None, filter_=None, opt_filter=None, kolumne=None,
                 place_holder_kwargs=None, obj=None):

        InputColumnSpec.__init__(self, col_name=col_name, doc=doc,
                                 label=label, validators=validators,
                                 filter_=filter_, opt_filter=opt_filter,
                                 kolumne=kolumne)
        PlaceHolderColumnSpec.__init__(self, template_fname=template_fname,
                                       place_holder_kwargs=place_holder_kwargs,
                                       record=record)

    @property
    def field(self, column_spec):
        ret = super(InputPlaceHolderColumnSpec, self).make_field(column_spec)
        ret.widget = PlaceHolder(self.template_fname, self.record,
                                 self.place_holder_kwargs)
        return ret
