#-*- coding:utf-8 -*-
from flask.ext.babel import _

from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask.ext.databrowser.backends import Backend, Kolumne
from flask.ext.databrowser.exceptions import InvalidArgumentError
from flask.ext.databrowser.sa_utils import get_primary_key


class SABackend(Backend):
    def __init__(self, model, db, model_name="", hide_back_ref=True):
        self.model = model
        self.db = db
        super(SABackend, self).__init__(model_name or model.__name__)
        self._hide_back_ref = hide_back_ref
        self._primary_key = None

    def order_by(self, query, order_by, desc):
        order_criterion = self._get_last_sa_criterion(order_by)
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

    @property
    def primary_key(self):
        if self._primary_key is None:
            self._primary_key = get_primary_key(self.model)
        return self._primary_key

    def get_column_doc(self, col_name):
        criterion = self._get_last_sa_criterion(col_name)
        return getattr(criterion, "doc", None)

    #TODO should rename to _get_last_sa_column
    def _get_last_sa_criterion(self, col_name):
        attr_name_list = col_name.split('.')
        last_model = self.model

        try:
            for attr_name in attr_name_list[:-1]:
                last_prop = getattr(last_model, attr_name).property
                last_model = last_prop.mapper.class_
            return getattr(last_model, attr_name_list[-1])
        except AttributeError:
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

        User's form won't display a select to specify the user's group enless
        you specify the 'group' relationship

        of course, back references are filtered if need
        """
        ret = []

        for p in self.model.__mapper__.iterate_properties:
            kol = SAKolumne(p)
            if kol.is_relationship():
                if not self.hide_back_ref or kol.not_back_ref():
                    ret.append(kol)
            else:
                if not kol.is_fk():
                    ret.append(kol)
        return ret

    def get_kolumn(self, col_name):
        return SAKolumne(getattr(self.model, col_name).property)

    def has_kolumn(self, col_name):
        return hasattr(self.model, col_name)


class SAKolumne(Kolumne):
    def __init__(self, property_):
        assert isinstance(property_, (ColumnProperty, RelationshipProperty,
                                      InstrumentedAttribute))
        if isinstance(property_, InstrumentedAttribute):
            self._property = property_.property
        self._property = property_

    def is_relationship(self):
        return hasattr(self._property, "direction")

    def remote_side(self):
        return self._property.mapper.class_

    def local_column(self):
        return self._property.local_remote_pairs[0][0]

    def not_back_ref(self):
        '''
        test if not is back reference
        '''
        return self._property.backref

    def is_fk(self):
        '''
        test if is foreign key column
        '''
        return not self.is_relationship() and \
            self._property.columns[0].foreign_keys

    @property
    def key(self):
        return self._property.key

    @property
    def direction(self):
        return self._property.direction.name
