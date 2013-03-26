# -*- coding: UTF-8 -*-
import numbers
from flask.ext.databrowser import extra_widgets
from flask.ext.databrowser import column_spec

class ValueConverter(object):
    """
    a converter from **plain value** (other than sqlalchemy.orm.attributes.InstrumentedAttribute)
    to widget (we don't need Field here, since we don't need validate the input). 
    note, since python is a dynamic language, we can't get the return type of
    a property until we get the value of the property, the rule is as following:
    """
    def __init__(self, obj, model_view=None):
        self.obj = obj
        self.model_view = model_view

    def __call__(self, v, col_spec=None):
        old_v = v
        css_class = None
        if not col_spec:
            w = extra_widgets.PlainText(unicode(v))
        else:
            obj = self.obj
            if self.model_view and col_spec and hasattr(v, "__mapper__"):
                from .utils import get_primary_key
                ref_col_spec = self.model_view.data_browser.create_object_link_column_spec(
                    v.__mapper__.class_, col_spec.label)
                if ref_col_spec:
                    obj = v
                    col_spec = ref_col_spec

            if col_spec.formatter:
                v = col_spec.formatter(v, obj)
            css_class = col_spec.css_class

            if col_spec.genre == column_spec.IMAGE:
                w = extra_widgets.Image(v, alt=col_spec.alt)
            elif col_spec.genre == column_spec.LINK:
                w = extra_widgets.Link((col_spec.anchor if isinstance(col_spec.anchor, basestring) else col_spec.anchor(old_v)) or v, href=v)
            elif col_spec.genre == column_spec.TABLE: 
                # TODO if v is a registered model, then a link should generated 
                w = extra_widgets.TableWidget(v, col_specs=col_spec.col_specs, model_view=self.model_view, sum_fields=col_spec.sum_fields)
            elif col_spec.genre == column_spec.UNORDERED_LIST:
                w = extra_widgets.ListWidget(v, item_col_spec=col_spec.item_col_spec)
            elif col_spec.genre == column_spec.PLACE_HOLDER:
                w = extra_widgets.PlaceHolder(col_spec.template_fname, v, self.obj)
            else: # plaintext
                # we try to convert it to link
                    w = extra_widgets.PlainText(unicode(v))

        class FakeField(object):
            def __init__(self, label, widget, css_class=None):
                self.label = label
                self.widget = widget
                self.type = "ReadOnlyField"
                self.css_class = css_class

            def __call__(self, **kwargs):
                if self.css_class:
                    kwargs["class"] = self.css_class
                return self.widget(self, **kwargs)

        return FakeField(dict(text=col_spec.label if col_spec else ""), widget=w, css_class=css_class)
