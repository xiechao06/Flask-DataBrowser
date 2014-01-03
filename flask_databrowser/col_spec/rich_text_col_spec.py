# -*- coding: utf-8 -*-
from flask.ext.databrowser.extra_fields import TinyMceField
from flask.ext.databrowser.col_spec import ColSpec


# we should provide a non-hacker way to hack them in template
class RichTextColSpec(ColSpec):

    as_input = True

    # TODO need default_value parameter
    def __init__(self, col_name, label=None, disabled=False,
                 doc=None, formatter=None, validators=None,
                 kolumne=None, data_browser=None, render_kwargs={}):
        """
        :param col_name: name of the kolumne

        .. code::python

            class GenreGrouper(Grouper):

                @property
                def options(self):
                    return ['male', 'femail']

                def group(self, record):
                    return record.genre

            will group the Person into male group and female group

        :param disabled: if this is a read only field
        :param doc: document of the kolumne
        :param formatter: a function the raw value of the kolumne to the
            representation
        :param label: lable of the kolumne
        :param validators: a list of wtforms' validators
        :param kolumne: underlying kolumne
        :param data_browser:
        :param render_kwargs: arguments used to render field by template
        engine, note, this argument is very important when you use your
        templates to render fields. Read
        'templates/__databrowser__/macro.html' to discover which keys are
        accepted
        :type render_kwargs: dict
        """
        ColSpec.__init__(self, col_name, doc=doc,
                         formatter=formatter, label=label,
                         render_kwargs=render_kwargs)
        self.disabled = disabled
        self.validators = validators or []
        self.kolumne = kolumne
        self.data_browser = data_browser

    def make_field(self, record=None, model_view=None):
        """
        convert to field
        """
        # note!!! use copy here, otherwise col_spec.validators will be changed
        return TinyMceField(label=self.label, validators=self.validators,
                            id=self.col_name)
    @property
    def remote_create_url(self):
        return None
