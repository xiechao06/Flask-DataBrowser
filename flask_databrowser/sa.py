#-*- coding:utf-8 -*-
from flask.ext.babel import _

from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask.ext.databrowser.backends import Backend, Kolumne
from flask.ext.databrowser.exceptions import InvalidArgumentError
from flask.ext.databrowser.sa_utils import get_primary_key


class SABackend(Backend):
    def __init__(self, model, db, model_name=""):
        self.model = model
        self.db = db
        super(SABackend, self).__init__(model_name or model.__name__)
        self._primary_key = None

    def order_by(self, query, order_by, desc):
        order_criterion = self._get_last_sa_criterion(order_by)
        if order_criterion is None:
            raise InvalidArgumentError(_("Invalid order by criterion '%(order_by)s'", order_by=order_by))
        if hasattr(order_criterion.property, 'direction'):
            order_criterion = order_criterion.property.local_remote_pairs[0][0]
        if desc:
            order_criterion = order_criterion.desc()
        return query.order_by(order_criterion)

    def scaffold_query(self, current_filters, order_by):
        def _get_joined_tables(col_names):
            joined_tables = set([])
            for col_name in col_names:
                attrs = col_name.split(".")
                last_join_model = self.model
                for rel in attrs[:-1]:
                    last_join_model = getattr(last_join_model, rel).property.mapper.class_
                    joined_tables.add(last_join_model)
            return joined_tables

        q = self.query
        col_names = [filter_.col_name for filter_ in current_filters]
        if order_by:
            col_names.append(order_by)
        for table in _get_joined_tables(col_names):
            q = q.join(table)
        return q

    @property
    def query(self):
        return self.model.query

    @property
    def primary_key(self):
        if self._primary_key is None:
            self._primary_key = get_primary_key(self.model)
        return self._primary_key

    def get_column_doc(self, col_name):
        criterion = self._get_last_sa_criterion(col_name)
        return getattr(criterion, "doc", None)

    def _get_last_sa_criterion(self, col_name):
        attr_name_list = col_name.split('.')
        last_model = self.model

        try:
            for attr_name in attr_name_list[:-1]:
                last_model = getattr(last_model, attr_name).property.mapper.class_
            return getattr(last_model, attr_name_list[-1])
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

    @property
    def kolumnes(self):
        def _filter_foreign_keys(p):
            # 不需要外键及多对多映射
            return p.local_remote_side[0][0].foreign_keys if hasattr(p, "direction") else not p.columns[0].foreign_keys

        return [SAKolumne(p) for p in self.model.__mapper__.iterate_properties if _filter_foreign_keys(p)]


class SAKolumne(Kolumne):
    def __init__(self, property_):
        assert isinstance(property_, (ColumnProperty, RelationshipProperty, InstrumentedAttribute))
        if isinstance(property_, InstrumentedAttribute):
            self._property = property_.property
        self._property = property_

    def is_relationship(self):
        return hasattr(self._property, "direction")

    def remote_side(self):
        return self._property.mapper.class_

    def local_column(self):
        return self._property.local_remote_pairs[0][0]

    @property
    def key(self):
        return self._property.key