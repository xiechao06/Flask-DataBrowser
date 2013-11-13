#-*- coding:utf-8 -*-
class Backend(object):
    def __init__(self, model_view, model_name=""):
        self.model_view = model_view
        self.model_name = model_name

    @property
    def query(self):
        """
        :return: a query object, which should at least support 4 methods:
            * count()
            * offset(<int>)
            * limit(<int>)
            * all()
            refer to `flask.ext.databrowser.Backend.get_list`_

        """
        raise NotImplementedError

    def scaffold_query(self, current_filters, order_by):
        return self.query

    def get_list(self, order_by, desc, filters, offset, limit):

        q = self.scaffold_query(filters, order_by)
        for filter_ in self.model_view.default_list_filters:
            if not filter_.model_view:
                filter_.model_view = self.model_view
            q = filter_(q)

        for filter_ in filters:
            if filter_.has_value():
                q = filter_(q)

        if order_by:
            q = self.order_by(q, order_by, desc)
        total_cnt = q.count()
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

        return total_cnt, q.all()

    def order_by(self, query, order_by, desc):
        raise NotImplementedError

    def get_column_doc(self, col_name):
        raise NotImplementedError

    @property
    def primary_key(self):
        raise NotImplementedError

    @property
    def columns(self):
        raise NotImplementedError

    def get_pk_value(self, obj):
        raise NotImplementedError

    def commit(self):
        pass

    def rollback(self):
        pass

    def get_items(self, pks):
        raise NotImplementedError


class Kolumne(object):
    pass