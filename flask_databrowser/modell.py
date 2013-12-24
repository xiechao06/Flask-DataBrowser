#-*- coding:utf-8 -*-


#TODO should rename to Typ
class Modell(object):
    def __init__(self, label=""):
        self.label = label

    @property
    def converter(self):
        raise NotImplementedError

    @property
    def query(self):
        """
        :return: a query object, which should at least support 4 methods:
            * count()
            * offset(<int>)
            * limit(<int>)
            * all()
            * first()
            * get(<int>)
            * one()
            refer to `flask.ext.databrowser.Backend.get_list`_

        NOTE!!! there's an implicit requirment: if the objects returned from
        these aforementioned methods are modified and after commit, the
        alternations will be persisted
        """
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    def scaffold_query(self, current_filters, order_by):
        #只做join_table的工作， 如果需要的话
        return self.query

    def get_list(self, order_by, desc, filters, offset, limit):
        #filters 包括默认的filters及当前运行的filters

        q = self.scaffold_query(filters, order_by)

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

    #TODO should be elminated, using get_kolumne(col_name).doc instead
    def get_column_doc(self, col_name):
        raise NotImplementedError

    @property
    def primary_key(self):
        raise NotImplementedError

    def get_pk_value(self, obj):
        raise NotImplementedError

    def commit(self):
        pass

    def rollback(self):
        pass

    def get_items(self, pks):
        raise NotImplementedError

    @property
    def kolumnes(self):
        raise NotImplementedError

    def get_kolumne(self, col_name):
        raise NotImplementedError

    def has_kolumne(self, col_name):
        raise NotImplementedError

    def new_model(self):
        '''
        NOTE!!! there's an implicit requirment: if the object returned are
        modified and after commit, the alternations will be persisted
        '''
        raise NotImplementedError

    def delete_record(self, record):
        raise NotImplementedError

    def search_kolumne(self, col_name):
        raise NotImplementedError
