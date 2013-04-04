from sqlalchemy.orm.exc import NoResultFound

from wtforms import ValidationError


class Unique(object):
    """Checks field value unique against specified table field.

    :param db_session:
        A given SQAlchemy Session.
    :param model:
        The model to check unique against.
    :param column:
        The unique column.
    :param message:
        The error message.
    """
    field_flags = ('unique', )

    def __init__(self, db_session, model, column, message=None):
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message

    def __call__(self, form, field):
        try:
            obj = (self.db_session.query(self.model)
                   .filter(self.column == field.data).one())

            if not hasattr(form, '_obj') or not form._obj == obj:
                if self.message is None:
                    self.message = field.gettext("This field must be unique, but it already exists!")
                raise ValidationError(self.message)
        except NoResultFound:
            pass
