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
do_commit(User(name="Tom Cat", password="tc", group=group))
do_commit(User(name="Jerry Mouse", password="jm", group=group))
do_commit(User(name="Spike", password="s", group=group))
do_commit(User(name="Tyde", password="t", group=group))

group = do_commit(Group(name="StarTrek"))
do_commit(User(name="James T. Kirk", password="jtk", group=group))
do_commit(User(name="Spock", password="s", group=group))
do_commit(User(name='Leonard "Bones" McCoy', password="lbm", group=group))
do_commit(User(name='Montgomery "Scotty" Scott', password="mss", group=group))
do_commit(User(name='Hikaru Sulu', password="hs", group=group))
do_commit(User(name='Pavel Chekov', password="pc", group=group))
do_commit(User(name='Nyota Uhura', password="nu", group=group))
do_commit(User(name='Christine Chapel', password="cc", group=group))
do_commit(User(name='Janice Rand', password="jr", group=group))
