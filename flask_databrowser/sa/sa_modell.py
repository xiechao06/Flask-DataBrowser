# -*- coding: utf-8 -*-
from flask.ext.babel import _
from werkzeug import cached_property
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from flask.ext.databrowser.modell import Modell
from flask.ext.databrowser.exceptions import InvalidArgumentError
from flask.ext.databrowser.sa.sa_utils import get_primary_key
from flask.ext.databrowser.sa import SAKolumne


class SAModell(Modell):

    def __init__(self, model, db, label="", hide_back_ref=True):
        self.model = model
        self.db = db
        super(SAModell, self).__init__(label or model.__name__)
        self._hide_back_ref = hide_back_ref

    @property
    def name(self):
        return self.model.__name__

    @property
    def token(self):
        return ".".join([self.model.__module__, self.name])

    def order_by(self, query, order_by, desc):
        order_criterion = self._get_last_sa_column(order_by)
        if order_criterion is None:
            err_msg = _("Invalid order by criterion '%(order_by)s'",
                        order_by=order_by)
            raise InvalidArgumentError(err_msg)
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
                    last_prop = getattr(last_join_model, rel).property
                    last_join_model = last_prop.mapper.class_
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

    @cached_property
    def primary_key(self):
        return get_primary_key(self.model)

    def get_column_doc(self, col_name):
        criterion = self._get_last_sa_column(col_name)
        return getattr(criterion, "doc", None)

    def _get_last_sa_column(self, col_name):
        attr_name_list = col_name.split('.')
        last_model = self.model

        try:
            for attr_name in attr_name_list[:-1]:
                last_prop = getattr(last_model, attr_name).property
                last_model = last_prop.mapper.class_
            ret = getattr(last_model, attr_name_list[-1])
            if isinstance(ret, (ColumnProperty, RelationshipProperty,
                                InstrumentedAttribute)):
                return ret
        except AttributeError:
            return None

    def search_kolumne(self, col_name):
        col_def = self._get_last_sa_column(col_name)
        if col_def:
            return SAKolumne(col_def, self.db)
        return None

    #TODO NO NEED ANY MORE
    @property
    def columns(self):
        return list(self.model.__table__.columns)

    def get_pk_value(self, obj):
        return getattr(obj, self.primary_key)

    def commit(self):
        self.db.session.commit()

    def rollback(self):
        self.db.session.rollback()

    def add(self, item):
        self.db.session.add(item)

    def get_items(self, pks):
        criterion = getattr(self.model, self.primary_key).in_(pks)
        return self.query.filter(criterion).all()

    @property
    def kolumnes(self):
        """
        :return: a list of Kolumne, won't return foreign keys, that means,
        in the following Model:

        ..code::python

            class User(db.Model):

                name = db.Column(db.String(32), nullable=False, unique=True)
                group_id = db.Column(db.Integer, db.ForeignKey('TB_GROUP.id'))
                # omit group = db.relationship("Group")

        User's form won't display a select to specify the user's group unless
        you specify the 'group' relationship

        of course, back references are filtered if need
        """
        ret = []

        for p in self.model.__mapper__.iterate_properties:
            kol = SAKolumne(p, self)
            if kol.is_relationship():
                if not self._hide_back_ref or kol.not_back_ref():
                    ret.append(kol)
            else:
                if not kol.is_fk():
                    ret.append(kol)
        return ret

    @property
    def properties(self):
        return [SAKolumne(p, self.db) for p in
                self.model.__mapper__.iterate_properties]

    def get_kolumne(self, col_name):
        if self.has_kolumne(col_name):
            return SAKolumne(getattr(self.model, col_name), self.db)
        return None

    def has_kolumne(self, col_name):
        return hasattr(self.model, col_name) and \
            isinstance(getattr(self.model, col_name),
                       InstrumentedAttribute)

    @property
    def session(self):
        return self.db.session

    def new_model(self):
        return self.model()

    def delete_record(self, record):
        self.db.session.delete(record)
