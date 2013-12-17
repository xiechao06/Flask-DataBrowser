# -*- coding: UTF-8 -*-
import types
from basemain import db
from models import User, Group, Car, Log

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
tom = do_commit(User(name="Tom Cat", password="tc", group=group, age=12, pic_path='a.jpg'))
do_commit(User(name="Jerry Mouse", password="jm", group=group, age=13))
do_commit(User(name="Spike", password="s", group=group, age=14))
do_commit(User(name="Tyde", password="t", group=group, age=15))

group = do_commit(Group(name="StarTrek"))
do_commit(User(name="James T. Kirk", password="jtk", group=group, age=16))
do_commit(User(name="Spock", password="s", group=group, age=17))
do_commit(User(name='Leonard "Bones" McCoy', password="lbm", group=group, age=18))
do_commit(User(name='Montgomery "Scotty" Scott', password="mss", group=group, age=19))
do_commit(User(name='Hikaru Sulu', password="hs", group=group, age=20))
do_commit(User(name='Pavel Chekov', password="pc", group=group, age=21))
do_commit(User(name='Nyota Uhura', password="nu", group=group, age=22))
do_commit(User(name='Christine Chapel', password="cc", group=group, age=23))
do_commit(User(name='Janice Rand', password="jr", group=group, age=24))

car = do_commit(Car(model="BMW 3li", owner=tom))
car = do_commit(Car(model="Benz S600", owner=tom))
