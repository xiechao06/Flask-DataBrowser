# -*- coding: UTF-8 -*-
from wtforms.widgets import FileInput

from flask.ext.databrowser import extra_widgets
from flask.ext.databrowser import col_spec
from flask.ext.databrowser.col_spec import LinkColumnSpec, ImageColumnSpec, PlaceHolderColumnSpec, TableColumnSpec, FileColumnSpec


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
        if not col_spec:
            col_spec = col_spec.ColumnSpec("")
        obj = self.obj
        # convert relationshipt to link
        #if self.model_view and hasattr(v, "__mapper__"):
        #    ref_col_spec = self.model_view.data_browser.get_object_link_column_spec(
        #        v.__mapper__.class_, self.model_view.__column_labels__.get(col_spec.col_name, col_spec.col_name) if (
        #            col_spec.label is None) else col_spec.label)
        #    if ref_col_spec:
        #        obj = v # why we do this, see ModelView.create_object_link_column_spec
        #        if col_spec and col_spec.genre == col_spec.PLAIN_TEXT:
        #            if col_spec.formatter:
        #                def _Anchor(col_spec, obj):
        #                    def _anchor(v):
        #                        return col_spec.formatter(v, obj)
        #
        #                    return _anchor
        #
        #                ref_col_spec.anchor = _Anchor(col_spec, self.obj)
        #        col_spec = ref_col_spec

        if col_spec.formatter:
            v = col_spec.formatter(v, obj)
        css_class = col_spec.css_class

        if isinstance(col_spec, LinkColumnSpec):
            anchor = col_spec.anchor if isinstance(col_spec.anchor, basestring) else col_spec.anchor(old_v)
            if anchor is None:
                anchor = v
            w = extra_widgets.Link(anchor, href=v)
        elif isinstance(col_spec, ImageColumnSpec):
            w = extra_widgets.Image(v, alt=col_spec.alt)
        elif isinstance(col_spec, TableColumnSpec):
        ## TODO if v is a registered model, then a link should generated
            w = extra_widgets.TableWidget(v, col_specs=col_spec.col_specs, model_view=self.model_view,
                                          sum_fields=col_spec.sum_fields, preprocess=col_spec.preprocess)
        #elif col_spec.genre == col_spec.UNORDERED_LIST:
        #    w = extra_widgets.ListWidget(v, item_col_spec=col_spec.item_col_spec, model_view=self.model_view,
        #                                 compressed=col_spec.compressed, item_css_class=col_spec.item_css_class)
        elif isinstance(col_spec, PlaceHolderColumnSpec):

        #    options = []
        #    try:
        #        col_def = operator.attrgetter(col_spec.col_name)(self.model_view.model)
        #        options = [o for o in col_spec.filter_(self.model_view._session.query(col_def.property.mapper.class_))]
        #    except AttributeError:
        #        pass
        #
            w = extra_widgets.PlaceHolder(col_spec.template_fname,v, self.obj)
        #elif col_spec.genre == col_spec.SELECT:
        #    w = extra_widgets.SelectWidget(v, self.obj, self.model_view, choices=col_spec.choices)
        #else:  # plaintext
        #    # we try to convert it to link
        elif isinstance(col_spec, FileColumnSpec):
            w = FileInput()
        else:
            w = extra_widgets.PlainText(unicode(v) if v is not None else "")
        #

        class ItemField(object):
            def __init__(self, label, name, widget, css_class=None, description=None, id=None, read_only=True, form_width_class=""):
                self.label = label
                self.name = name
                self.id = id or name
                self.widget = widget
                self.type = "ReadOnlyField" if read_only else "MyInputField"
                self.css_class = css_class
                self.description = description
                self.form_width_class = form_width_class

            def __call__(self, **kwargs):
                if self.css_class:
                    if "class" in kwargs:
                        kwargs["class"] = " ".join([kwargs["class"], self.css_class])
                    else:
                        kwargs["class"] = self.css_class
                return self.widget(self, **kwargs)
        description = col_spec.doc

        label = self.model_view.column_labels.get(col_spec.col_name, col_spec.col_name) if (
            col_spec.label is None) else col_spec.label
        return ItemField(dict(text=label), name=col_spec.col_name if col_spec else "", widget=w, css_class=css_class,
                         description=description, read_only=getattr(col_spec, "read_only", True),
                         form_width_class=getattr(col_spec, "form_width_class", ""))

