
import numbers
from wtforms.fields import Field
from flask.ext.databrowser import extra_widgets
from flask.ext.databrowser.utils import disabled_field_or_widget
from flask.ext.databrowser import column_spec 

class ValueConverter(object):
    """
    a converter from **plain value** (other than sqlalchemy.orm.attributes.InstrumentedAttribute)
    to widget (we don't need Field here, since we don't need validate the input). 
    note, since python is a dynamic language, we can't get the return type of
    a property until we get the value of the property, the rule is as following:
    """
    @disabled_field_or_widget
    def __call__(self, v, col_spec=None):
        old_v = v
        if col_spec:
            if col_spec.formatter:
                v = col_spec.formatter(v, None)
        w = None
        if isinstance(v, basestring) or isinstance(v, numbers.Number):
            if col_spec:
                if col_spec.genre == column_spec.IMAGE:
                    w = extra_widgets.Image(v, alt=col_spec.alt)
                elif col_spec.genre == column_spec.LINK:
                    w = extra_widgets.Link((col_spec.anchor if isinstance(col_spec.anchor, basestring) else col_spec.anchor(old_v)) or v, href=v)
        elif hasattr(v, "__iter__") or isinstance(v, dict):
            if isinstance(v, dict):
                v = v.items()
            if col_spec and col_spec.genre == column_spec.TABLE:
                # TODO if v is a registered model, then a link should generated 
                w = extra_widgets.TableWidget(v, col_spec)
            else:
                w = extra_widgets.ListWidget(extra_widgets.PlainText(unicode(i)) for i in v)
        if not w:
            # TODO if v is a registered model, then a link should be generated
            w = extra_widgets.PlainText(v)

        class FakeField(object):
            def __init__(self, label, widget):
                self.label = label
                self.widget = widget
                self.type = "ReadOnlyField"

            def __call__(self, **kwargs):
                return self.widget(self, **kwargs)

        return FakeField(dict(text=col_spec.label if col_spec else ""), widget=w)
