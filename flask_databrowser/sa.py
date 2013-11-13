#-*- coding:utf-8 -*-
from flask.ext.babel import _
from sqlalchemy import Column
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask.ext.databrowser.backends import Backend, Kolumne
from flask.ext.databrowser.exceptions import InvalidArgumentError
from flask.ext.databrowser.sa_utils import get_primary_key


class SABackend(Backend):
    def __init__(self, model, db, model_view, model_name=""):
        self.model = model
        self.db = db
        super(SABackend, self).__init__(model_view, model_name or model.__name__)
        self.__primary_key__ = None

    def order_by(self, query, order_by, desc):
        order_criterion = self._get_last_sa_column(order_by)
        if not order_criterion:
            raise InvalidArgumentError(_("Invalid order by criterion '%(order_by)s'", order_by=order_by))
        if hasattr(order_criterion.property, 'direction'):
            order_criterion = order_criterion.property.local_remote_pairs[0][0]
        if desc:
            order_criterion = order_criterion.desc()
        return query.order_by(order_criterion)

    def scaffold_query(self, current_filters, order_by):
        #TODO
        return self.query

    @property
    def query(self):
        return self.model.query

    @property
    def primary_key(self):
        if self.__primary_key__ is None:
            self.__primary_key__ = get_primary_key(self.model)
        return self.__primary_key__

    def get_column_doc(self, col_name):
        last_column = self._get_last_sa_column(col_name)
        return last_column.doc if last_column else ""

    def _get_last_sa_column(self, col_name):
        attr_name_list = col_name.split('.')
        last_model = self.model

        try:
            for attr_name in attr_name_list[:-1]:
                last_model = getattr(last_model, attr_name).property.mapper.class_
            return getattr(last_model, attr_name_list[-1]).property.columns[0]
        except AttributeError:
            return None

    @property
    def columns(self):
        return list(self.model.__table__.columns)

    def get_pk_value(self, obj):
        return getattr(obj, self.primary_key)

    def commit(self):
        self.db.session.commit()

    def rollback(self):
        self.db.session.rollback()

    def get_items(self, pks):
        return self.query.filter(getattr(self.model, self.primary_key).in_(pks)).all()


class SAKolumne(Kolumne):
    def __init__(self, obj):
        assert isinstance(obj, (ColumnProperty, RelationshipProperty, Column, InstrumentedAttribute))
        self.__obj__ = obj

    def is_relationship(self):
        if isinstance(self.__obj__, RelationshipProperty):
            return True
        else:
            return False

    def remote_side(self):
        if isinstance(self.__obj__, RelationshipProperty):
            return self.__obj__.remote_side
        else:
            return None


    @property
    def key(self):
        return self.__obj__.key