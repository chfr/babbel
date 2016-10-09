# coding=utf-8
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from flask import g
import pytz

Base = declarative_base()


def populate_db(db_session):
    from models import User, Message

    if User.query.count() > 0:  # Quick and dirty way to make sure we only run this when the DB is empty
        print "User table non-empty, not populating database"
        return

    print "Populating database with dummy data..."

    a = User(username="a")
    db_session.add(a)
    db_session.commit()
    b = User(username="b")
    db_session.add(b)
    db_session.commit()
    c = User(username="c")
    db_session.add(c)
    db_session.commit()

    m = Message(a, b, u"Hej, a skriver till b nu")
    db_session.add(m)
    db_session.commit()

    m = Message(b, c, u"Hej från b till c i maj 2016", datetime(2016, 5, 7, 13, 37, 0, tzinfo=pytz.utc))
    db_session.add(m)
    db_session.commit()

    m = Message(b, c, u"Hej, b till c lite senare i maj 2016", datetime(2016, 5, 7, 14, 37, 0, tzinfo=pytz.utc))
    db_session.add(m)
    db_session.commit()

    print "Database has been populated"
