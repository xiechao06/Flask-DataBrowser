# -*- coding: utf-8 -*-
from flask.ext.databrowser.col_spec import ColSpec


# we should provide a non-hacker way to hack them in template
class InputColSpec(ColSpec):

    as_input = True

    # TODO need default_value parameter
    def __init__(self, col_name, label=None, group_by=None, disabled=False, doc=None,
                 formatter=None, filter_=None,
                 opt_filter=None,  validators=None,
                 kolumne=None, data_browser=None, entry_formatter=None,
                 render_kwargs={}, widget=None):
        """
        :param col_name: name of the kolumne
        :param group_by: should be instance of Grouper

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
        :param filter_: a function to filter the options query object
        :param opt_filter: a function to filter the options
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
        self.group_by = group_by
        self.disabled = disabled
        self.filter_ = filter_ or (lambda v: v)
        self.opt_filter = opt_filter or (lambda obj: True)
        self.validators = validators or []
        self.kolumne = kolumne
        self.data_browser = data_browser
        self.entry_formatter = entry_formatter
        self.widget = widget

    @property
    def grouper_input_name(self):
        """
        name of the grouper input html element's name
        """
        return self.col_name + "." + self.group_by.__class__.__name__

    def make_field(self, record=None, model_view=None):
        """
        convert to field
        """
        # note!!! use copy here, otherwise col_spec.validators will be changed
        ret = self.kolumne.make_field(self)
        if self.widget:
            ret.kwargs['widget'] = self.widget
        return ret

    @property
    def remote_create_url(self):
        if self.kolumne.is_relationship() and \
           self.kolumne.direction == 'MANYTOONE':
            remote_side = self.kolumne.remote_side
            return self.data_browser.search_create_url(remote_side,
                                                       self.col_name)


def input_col_spec_from_kolumne(k):
    return InputColSpec(k.key, doc=k.doc, kolumne=k)
