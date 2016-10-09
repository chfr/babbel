# coding=utf-8
from datetime import datetime

import pytz
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, TypeDecorator
from sqlalchemy.orm import relationship

from database import Base

MESSAGE_MAXLEN = 100
BEGINNING_OF_TIME = datetime(1987, 4, 2, 0, 0, 1, tzinfo=pytz.utc)


class AwareDateTime(TypeDecorator):
    """
    Results returned as aware datetimes, not naive ones.
    http://stackoverflow.com/a/23397776
    """

    impl = DateTime

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=pytz.utc)


class User(Base):
    """Represents a user. A user is nly identified by their user name. Each user also has a last refresh timestamp."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    last_fetch = Column(AwareDateTime(timezone=True), nullable=False)

    def __init__(self, username=None, last_fetch=None):
        self.username = username
        if isinstance(last_fetch, datetime):
            self.last_fetch = last_fetch
        else:
            self.last_fetch = BEGINNING_OF_TIME

    def __repr__(self):
        return '<User %d: %s (last seen %s)>' % (self.id, self.username, self.last_fetch.strftime("%Y-%m-%d %H:%M:%S"))


class Message(Base):
    """Represents a message. A message has a sender, a receiver, the actual message contents and a timestamp."""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)

    sender_id = Column("sender_id", Integer, ForeignKey("users.id"), nullable=False)
    sender = relationship("User", foreign_keys=[sender_id])

    receiver_id = Column("receiver_id", Integer, ForeignKey("users.id"), nullable=False)
    receiver = relationship("User", foreign_keys=[receiver_id])

    message = Column(String(MESSAGE_MAXLEN), nullable=False)
    timestamp = Column(AwareDateTime(timezone=True), nullable=False)

    def __init__(self, sender, receiver, message, timestamp=None):
        self.receiver = receiver
        self.sender = sender
        self.message = message
        if isinstance(timestamp, datetime):
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now(tz=pytz.utc)

    def __repr__(self):
        return "Message %d: %s to %s (%s): %s" % (self.id,
                                                  self.sender.username,
                                                  self.receiver.username,
                                                  self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                                  self.message)
