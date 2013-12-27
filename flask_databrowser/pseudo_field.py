# -*- coding: UTF-8 -*-
from flask import request
from wtforms import fields
from . import extra_widgets
from flask.ext.databrowser.constants import BACK_URL_PARAM


class PseudoField(fields.Field):
    '''
    this is actually not wtforms' field, but a field only used to generate
    html
    '''
    def __init__(self, label, id, widget, record, col_spec, model_view,
                 description='',
                 render_kwargs={}, **kwargs):
        super(PseudoField, self).__init__(label=label, id=id, widget=widget,
                                          **kwargs)
        self.description = description
        self.render_kwargs = render_kwargs
        self.col_spec = col_spec
        self.model_view = model_view
        self.record = record

        self._normalize_formatter()

    def _normalize_formatter(self):
        if not self.col_spec.formatter:
            self.formatter = lambda v, obj: v
            if self.col_spec.col_name == self.model_view.modell.primary_key:
                self.formatter = lambda v, obj: \
                    (v,
                     self.model_view.url_for_object(self.record,
                                                    **{BACK_URL_PARAM:
                                                       request.url}))
                if not self.widget:
                    self.widget = extra_widgets.Link('_blank')
            else:
                kol = self.model_view.modell.search_kolumne(
                    self.col_spec.col_name)
                if kol and kol.is_relationship():
                    href = self.model_view.data_browser.search_obj_url(
                        kol.remote_side)
                    if href:  # could be reference to remote object
                        class _Formatter(object):
                            def __init__(self, kol, href):
                                self.remote_side = kol.remote_side
                                self.href = href

                            def __call__(self, v, obj):
                                if v is None:
                                    return None
                                pk = self.remote_side.get_pk_value(v)
                                return (v, self.href(pk))
                        self.formatter = _Formatter(kol, href)
                        if not self.widget:
                            # due to permission, although there do be a page
                            # of remote object, but current user can't see,
                            # so we won't display link to it
                            def _widget(field, **kwargs):
                                if field.data is None:
                                    return extra_widgets.PlainText()(field,
                                                                     **kwargs)
                                elif field.data[1] is None:
                                    field.data = field.data[0]
                                    return extra_widgets.PlainText()(field,
                                                                     **kwargs)
                                else:
                                    return extra_widgets.Link(
                                        '_blank')(field, **kwargs)
                            self.widget = _widget
        else:
            self.formatter = self.col_spec.formatter
        if not self.widget:
            self.widget = extra_widgets.PlainText()

    def __call__(self, **kwargs):
        css_class = self.render_kwargs.get('css_class', '')
        if 'class' in kwargs:
            kwargs["class"] = " ".join([kwargs["class"], css_class])
        else:
            kwargs["class"] = css_class
        return self.widget(self, **kwargs)

    @property
    def __read_only__(self):
        return True

    @property
    def __render_kwargs__(self):
        return self.render_kwargs

    def process_data(self, value):
        self.data = self.formatter(value, self.record)

    def _value(self):
        return self.data
