# -*- coding: utf-8 -*-
from flask.ext.databrowser.col_spec import ColSpec
from flask.ext.databrowser.extra_widgets import HtmlSnippet


class HtmlSnippetColSpec(ColSpec):

    def __init__(self, col_name, template, label=None, doc=None,
                 render_kwargs={}):
        super(HtmlSnippetColSpec, self).__init__(col_name, label=label,
                                                 doc=doc,
                                                 render_kwargs=render_kwargs)
        self.template = template

    def override_widget(self, obj):
        '''
        only when the form is bound with object, HtmlSnippet could be created
        '''
        return HtmlSnippet(template=self.template, obj=obj,
                           render_kwargs=self.render_kwargs)
