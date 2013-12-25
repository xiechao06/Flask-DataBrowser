# -*- coding: utf-8 -*-
from . import InputColSpec, HtmlSnippetColSpec


class InputHtmlSnippetColSpec(InputColSpec, HtmlSnippetColSpec):
    '''
    A column specification meant to use html snippet to generate input element
    Why it is here? why not just pass HtmlSnippet as the 'widget' parameter
    to ColSpec, that's because, HtmlSnippet is very special, it accepts more
    information other than just field to generate html
    '''

    #TODO render_kwargs is enough
    def __init__(self, col_name, template, label=None, doc=None,
                 validators=None, filter_=None, opt_filter=None, kolumne=None,
                 render_kwargs={}):
        super(InputHtmlSnippetColSpec, self).__init__(
            col_name=col_name,
            doc=doc,
            label=label,
            validators=validators,
            filter_=filter_,
            opt_filter=opt_filter,
            kolumne=kolumne,
            render_kwargs=render_kwargs)
        self.template = template

    def make_field(self, record=None, model_view=None):
        return HtmlSnippetColSpec.make_field(self, record, model_view)
