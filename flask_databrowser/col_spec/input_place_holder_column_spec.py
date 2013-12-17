# -*- coding: utf-8 -*-
from . import InputColSpec


class InputPlaceHolderColumnSpec(InputColSpec):
    #TODO render_kwargs is enough
    def __init__(self, col_name, template_fname, label=None, doc=None,
                 validators=None, filter_=None, opt_filter=None, kolumne=None,
                 place_holder_kwargs=None):
        InputColSpec.__init__(self, col_name=col_name, doc=doc,
                                 label=label, validators=validators,
                                 filter_=filter_, opt_filter=opt_filter,
                                 kolumne=kolumne)
        self.template_fname = template_fname
        self.place_holder_kwargs = place_holder_kwargs or {}
        self.recode = None

    @property
    def field(self):
        from flask.ext.databrowser.extra_widgets import PlaceHolder
        ret = self.kolumne.make_field(self)
        ret.widget = PlaceHolder(self.template_fname,  None, self.recode,
                                 **self.place_holder_kwargs)
        return ret
