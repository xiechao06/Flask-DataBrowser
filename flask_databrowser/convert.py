# -*- coding: UTF-8 -*-
import operator

from flask.ext.databrowser import extra_widgets
from flask.ext.databrowser import column_spec
from flask.ext.databrowser.utils import get_description


class ValueConverter(object):
    """
    a converter from **plain value** (other than sqlalchemy.orm.attributes.InstrumentedAttribute)
    to widget (we don't need Field here, since we don't need validate the input). 
    note, since python is a dynamic language, we can't get the return type of
    a property until we get the value of the property, the rule is as following:
    """
    def __init__(self, obj, model_view):
        self.obj = obj
        self.model_view = model_view

    def __call__(self, v, col_spec=None):
        old_v = v
        css_class = None
        if not col_spec:
            col_spec = column_spec.ColumnSpec("")
        convert_to_link = False
        obj = self.obj
        # convert relationshipt to link
        if self.model_view and hasattr(v, "__mapper__"):
            ref_col_spec = self.model_view.data_browser.get_object_link_column_spec(
                v.__mapper__.class_, self.model_view.__column_labels__.get(col_spec.col_name, col_spec.col_name) if (col_spec.label is None) else col_spec.label)
            if ref_col_spec:
                obj = v # why we do this, see ModelView.create_object_link_column_spec
                if col_spec and col_spec.genre == column_spec.PLAIN_TEXT:
                    if col_spec.formatter:
                        def _Anchor(col_spec, obj):
                            def _anchor(v):
                                return col_spec.formatter(v, obj)
                            return _anchor
                        ref_col_spec.anchor = _Anchor(col_spec, self.obj)
                col_spec = ref_col_spec
                convert_to_link = True

        if col_spec.formatter:
            v = col_spec.formatter(v, obj)
        css_class = col_spec.css_class

        if col_spec.genre == column_spec.IMAGE:
            w = extra_widgets.Image(v, alt=col_spec.alt)
        elif col_spec.genre == column_spec.LINK:
            anchor = col_spec.anchor if isinstance(col_spec.anchor, basestring) else col_spec.anchor(old_v)
            if anchor is None:
                anchor = v 
            w = extra_widgets.Link(anchor, href=v)
        elif col_spec.genre == column_spec.TABLE: 
            # TODO if v is a registered model, then a link should generated 
            w = extra_widgets.TableWidget(v, col_specs=col_spec.col_specs, model_view=self.model_view,
                                          sum_fields=col_spec.sum_fields, preprocess=col_spec.preprocess)
        elif col_spec.genre == column_spec.UNORDERED_LIST:
            w = extra_widgets.ListWidget(v, item_col_spec=col_spec.item_col_spec, model_view=self.model_view,
                                         compressed=col_spec.compressed, item_css_class=col_spec.item_css_class)
        elif col_spec.genre == column_spec.PLACE_HOLDER:
            options = []
            col_def = operator.attrgetter(col_spec.col_name)(self.obj.__class__)
            if hasattr(col_def.property, 'direction'):
                options = [o for o in col_spec.filter_(self.model_view.session.query(col_def.property.mapper.class_))]
            w = extra_widgets.PlaceHolder(col_spec.template_fname, v, self.obj, self.model_view, options=options)
        elif col_spec.genre == column_spec.SELECT:
            w = extra_widgets.SelectWidget(v, self.obj, self.model_view, choices=col_spec.choices)
        else:  # plaintext
            # we try to convert it to link
            w = extra_widgets.PlainText(unicode(v) if v is not None else "", trunc=col_spec.trunc)

        class FakeField(object):
            def __init__(self, label, name, widget, css_class=None, description=None):
                self.label = label
                self.name = name
                self.widget = widget
                self.type = "ReadOnlyField"
                self.css_class = css_class
                self.description = description

            def __call__(self, **kwargs):
                if self.css_class:
                    kwargs["class"] = self.css_class
                return self.widget(self, **kwargs)

        description = get_description(self.model_view, col_spec.col_name, self.obj, col_spec)
        label = self.model_view.__column_labels__.get(col_spec.col_name, col_spec.col_name) if (col_spec.label is None) else col_spec.label
        return FakeField(dict(text=label), name=col_spec.col_name if col_spec else "", widget=w, css_class=css_class, description=description)

