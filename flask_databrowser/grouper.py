# -*- coding: utf-8 -*-


class Grouper(object):

    @property
    def options(self):
        raise NotImplementedError

    def group(self, record):
        raise NotImplementedError


class SAPropertyGrouper(Grouper):
    '''
    this is a group created from a sa property. for example:

    .. code::python

        class Product(SAModel):
            # ...
            product_type_id = db.Column(db.Integer,
                                        db.ForeignKey("TB_PRODUCT_TYPE.id"))
            product_type = db.relationship("ProductType", backref="products")
            # ...

        class ProductType(SAModel):
            __tablename__ = 'TB_PRODUCT_TYPE'

        class Order(SAModel):
            product_id = db.Column(db.Integer, db.ForeignKey("TB_PRODUCT.id"))
            product = db.relationship("Product")

        grouper = SAPropertyGrouper(Product.product_type)

    this grouper will group products by product type when create/edit Order
    '''

    def __init__(self, property_, db):
        self._property = property_
        self._db = db

    @property
    def options(self):
        return self._property.class_.query.all()

    def group(self, record):
        #TODO unimplemeted
        pass
