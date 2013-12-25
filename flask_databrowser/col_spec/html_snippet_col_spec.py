# -*- coding: utf-8 -*-
from flask.ext.databrowser.col_spec import ColSpec
from flask.ext.databrowser.pseudo_field import PseudoField
from flask.ext.databrowser.extra_widgets import HtmlSnippet


class HtmlSnippetColSpec(ColSpec):

    def __init__(self, col_name, template, label=None, doc=None,
                 render_kwargs={}):
        super(HtmlSnippetColSpec, self).__init__(col_name, label=label,
                                                 doc=doc,
                                                 render_kwargs=render_kwargs)
        self.template = template

    def make_field(self, record=None, model_view=None):
        widget = HtmlSnippet(template=self.template, obj=record,
                             render_kwargs=self.render_kwargs)
        return PseudoField(self.label, self.col_name,
                           record=record,
                           model_view=model_view,
                           widget=widget,
                           description=self.doc,
                           col_spec=self,
                           render_kwargs=self.render_kwargs)
