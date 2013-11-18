# -*- coding: utf-8 -*-
from flask.ext.databrowser.column_spec import ColumnSpec
from flask.ext.databrowser.grouper import Grouper


#TODO the attribute form_width_class and css_class is obsfucated,
# we should provide a non-hacker way to hack them in template
class InputColumnSpec(ColumnSpec):

    def __init__(self, col_name, group_by=None, read_only=False, doc=None,
                 formatter=None, label=None, css_class="", filter_=None,
                 opt_filter=None,  validators=None,  form_width_class=None,
                 kolumne=None, data_browser=None):
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

        :param read_only: if this is a read only field
        :param doc: document of the kolumne
        :param formatter: a function the raw value of the kolumne to the
            representation
        :param label: lable of the kolumne
        :param css_class: css class of the kolumne
        :param filter_: a function to filter the options query object
        :param opt_filter: a function to filter the options
        :param validators: a list of wtforms' validators
        :param form_width_class: ...
        :param kolumne: underlying kolumne
        :param data_browser:
        """
        super(InputColumnSpec, self).__init__(col_name, doc=doc,
                                              formatter=formatter, label=label,
                                              css_class=css_class,
                                              form_width_class=
                                              form_width_class)
        assert isinstance(group_by, Grouper)
        self.group_by = group_by
        self.read_only = read_only
        self.filter_ = filter_ or (lambda v: v)
        self.opt_filter = opt_filter or (lambda obj: True)
        self.validators = validators or []
        self.kolumne = kolumne
        self.data_browser = data_browser

    @property
    def grouper_input_name(self):
        '''
        name of the grouper input html element's name
        '''
        return self.col_name + "." + self.group_by.__class__.__name__

    @property
    def field(self):
        '''
        convert to field
        '''
        # note!!! use copy here, otherwise col_spec.validators will be changed
        return self.kolumne.make_field(self)

    @property
    def remote_create_url(self):
        if self.kolumne.is_relationship():
            remote_side = self.kolumne.remote_side
            return self.data_browser.search_create_url(remote_side,
                                                       self.col_name)


def input_column_spec_from_kolumne(k):
    #TODO use kolumne instead of property
    return InputColumnSpec(k.key, doc=k.doc, kolumne=k)
