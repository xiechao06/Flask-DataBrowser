#-*- coding:utf-8 -*-


# I fake a form since I won't compose my fields and get the
# hidden_tag (used to generate csrf) from model's form
import wtforms


class FakeForm(object):
    def __init__(self, model_form, fields):
        class FakeField(object):
            def __init__(self, field):
                self.field = field

            def __getattr__(self, item):
                return getattr(self.field, item)

            def __call__(self, *args, **kwargs):
                if self.field.type == 'BooleanField':
                    form_control_div = "<div class='checkbox'>%s</div>"
                    return form_control_div % self.field(**kwargs)
                else:
                    def _add_class(kwargs, _class):
                        kwargs["class"] = " ".join((kwargs["class"], _class)) if kwargs.get("class") else _class

                    _add_class(kwargs, "form-control" if self.is_input_field else "form-control-static")
                    return self.field(**kwargs)

            @property
            def is_input_field(self):
                return isinstance(self.field.widget, (wtforms.widgets.Input, wtforms.widgets.Select,
                                                      wtforms.widgets.TextArea)) \
                    and self.field.type not in ["ReadOnlyField", "FileField"]

            @property
            def form_width_class(self):
                initial = getattr(self.field, "form_width_class", "")
                if initial:
                    return initial
                if self.is_input_field:
                    return "col-lg-3"
                label = getattr(self.field, "label")
                if getattr(label, "text", None) or label.get("text"):
                    return "col-lg-10"
                return "col-lg-12"

        self.model_form = model_form
        self.fields = [FakeField(field) for field in fields]
        self.field_map = {}
        for field in self.fields:
            self.field_map[field.name] = field

    def __iter__(self):
        return iter(self.fields)

    def __getitem__(self, name):
        return self.field_map[name]

    def hidden_tag(self):
        return self.model_form.hidden_tag()

    def is_submitted(self):
        return self.model_form.is_submitted()

    @property
    def errors(self):
        return self.model_form.errors

    @property
    def has_file_field(self):
        return self.model_form.has_file_field