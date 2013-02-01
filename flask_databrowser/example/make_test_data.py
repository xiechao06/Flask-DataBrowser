# -*- coding: UTF-8 -*-
import types
from basemain import db
from models import User, Group

def do_commit(obj, action="add"):
    if action == "add":
        if isinstance(obj, types.ListType) or isinstance(obj, types.TupleType):
            db.session.add_all(obj)
        else:
            db.session.add(obj)
    elif action == "delete":
        db.session.delete(obj)
    db.session.commit()
    return obj

db.create_all()

group = do_commit(Group(name="Tom&Jerry"))
do_commit(User(name="Tom Cat", password="tc", groups=[group]))
do_commit(User(name="Jerry Mouse", password="jm", groups=[group]))
do_commit(User(name="Spike", password="s", groups=[group]))
do_commit(User(name="Tyde", password="t", groups=[group]))
