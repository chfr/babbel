# coding=utf-8
from flask import Flask, escape, request
from flask_restful import reqparse, abort, Api, Resource
from datetime import datetime, timedelta
import pytz
from dateutil import parser
from urllib import quote_plus
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from database import Base, populate_db
from models import User, Message, BEGINNING_OF_TIME, MESSAGE_MAXLEN
from views import views

app = Flask(__name__)
api = Api(app)

app.register_blueprint(views)

app.secret_key = "5"  # Guaranteed random by fair dice roll

app.config["DEBUG"] = False

db_session = None


def get_user_message_by_id(user, msg_id, fail_silently=False):
    """
    Retrieves a specific message. Returns 400 Bad Request or 404 Not Found for invalid requests.
    :param user: a User object representing the recipient of the requested message
    :param msg_id: the id of the specific message. The message's recipient has to be the specified user.
    This variable may be an integer or a string containing an integer.
    :param fail_silently: do not raise errors if a message could not be retrieved. Returns None instead if an error
    occurs.
    :return: The message, if found. If the message could not be found, an error will be raised.
    """

    if isinstance(msg_id, basestring):
        if not msg_id.isdigit():
            app.logger.warning(u"Non-digit message id string: %s" % msg_id)
            if fail_silently:
                return None
            else:
                abort(400)
        msg_id = int(msg_id)

    if not isinstance(msg_id, int):
        app.logger.warning(u"Non-digit message id: %s" % msg_id)
        if fail_silently:
            return None
        else:
            abort(400)

    message = Message.query.filter_by(receiver=user, id=msg_id).first()
    if not message:
        app.logger.warning(u"No message id %d found for user %s" % (msg_id, user.username))
        if fail_silently:
            return None
        else:
            abort(404)

    return message


def get_user_or_error(username, error=404):
    """
    Retrieves a User object based on a user name. Raises an error if the specified user does not exist.
    :param username: a string containing the user name
    :param error: the error to be thrown if the user does not exist. Default value is 404 (Not Found).
    :return: a User object
    """
    user = User.query.filter_by(username=username).first()
    if not user:
        app.logger.warning(u"User '%s' does not exist, returning %s" % (username, error))
        abort(error)

    return user


def dictify_message(message):
    return {
        "id": message.id,
        "sender": message.sender.username,
        "message": message.message,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S")}


def parse_datetime(arg):
    if not isinstance(arg, basestring):
        abort(400)
    try:
        return parser.parse(arg)
    # Possible exceptions:
    # http://dateutil.readthedocs.io/en/latest/parser.html#dateutil.parser.parse
    except ValueError:
        app.logger.error("ValueError: could not parse %r as a datetime value" % arg)
    except OverflowError:
        app.logger.error("OverflowError: parsed date exceeds the largest valid C integer on this system")

    abort(400)


# Used to validate POST data in MessageResource.post()
msg_post_parser = reqparse.RequestParser()
msg_post_parser.add_argument("receiver", type=unicode, required=True)
msg_post_parser.add_argument("message", type=unicode, required=True)


class MessageResource(Resource):
    """
    Resource representing a Message. Allowed methods are GET, POST and DELETE.
    """

    def get(self, username, msg_id):
        """
        If called without the msg_id parameter, all new messages since the user's last fetch are returned.
        If the msg_id parameter is present, the message identified by that id is returned.
        """
        app.logger.debug(u"GET MessageResource %s" % request.path)
        user = get_user_or_error(username)

        message = get_user_message_by_id(user, msg_id)

        return dictify_message(message)

    def post(self, username):
        """
        Stores a new message from the username specified in the URL to the user specified in the POST data.
        The POST data must contain the "receiver" and "message" fields.
        """
        app.logger.debug(u"POST MessageResource %s\nForm data:\n%s" % (request.path, request.form))
        user = get_user_or_error(username)

        args = msg_post_parser.parse_args()  # Raises 400 Bad Request if the POST data is invalid

        receiver_name = args["receiver"]
        receiver = get_user_or_error(receiver_name)

        message = args["message"]
        if len(message) > MESSAGE_MAXLEN:
            app.logger.warning("Message length exceeds MESSAGE_MAXLEN (%d), truncating" % MESSAGE_MAXLEN)
            # Not necessary with SQLite (https://sqlite.org/faq.html#q9) but it seems prudent nonetheless.
            message = message[:MESSAGE_MAXLEN]

        new_message = Message(sender=user, receiver=receiver, message=message, timestamp=datetime.now(tz=pytz.utc))
        db_session.add(new_message)
        db_session.commit()

        return "", 204  # 204 No Content

    def delete(self, username, msg_id=None):
        """
        Deletes a user's message(s), if the messages exist and the user is the recipient of the messages.
        If requested without any request body, the message id must be specified in the URL like so:
        http://chfr.net:8080/a/message/11/
        To delete multiple messages, include a request body with JSON data, containing a single list called "ids":
        { "ids": [1, 2, 3, 5] }
        Returns 204 if at least one deletion succeeded, otherwise 400 Bad Request.
        """
        app.logger.debug(u"DELETE MessageResource %s" % request.path)

        ids = []
        if msg_id is not None:
            ids.append(msg_id)

        data = request.get_json(force=True, silent=True)
        if data is not None and "ids" in data:
            ids.extend(data["ids"])

        user = get_user_or_error(username)

        deletion_succeeeded = False
        for msg_id in ids:
            message = get_user_message_by_id(user, msg_id, fail_silently=True)
            if message is None:
                app.logger.warning("Attempted deletion of message %s failed for user %s" % (msg_id, user.username))
            else:
                app.logger.debug("Deleting message with id %s" % message.id)
                db_session.delete(message)
                db_session.commit()
                deletion_succeeeded = True
        if deletion_succeeeded:
            return "", 204  # 204 No Content
        else:
            return "", 400  # 400 Bad Request


class MessageList(Resource):
    """
    Responds to GET requests with a list of messages, depending on GET parameters.
    """

    def get(self, username):
        """
        If requested without GET parameters, a list of new messages is returned.
        The requester may optionally use the "start" and "end" GET parameters to specify a date range. Any messages
        that were received within this date range will then be returned. Dates must be specified in ISO 8601 format
        (with time zone information) and URL encoded. An example request to retrieve messages for user "a" between the
        dates 2016-10-08T10:23:29.0+00:00 and 2016-10-08T10:23:50.828699+00:00:
        /a/messages/?start=2016-10-08T10%3A23%3A29.000000%2B00%3A00&end=2016-10-08T10%3A23%3A50.828699%2B00%3A00
        These date strings are horrible to construct by hand, so at /dates/ there's a handy helper.
        """
        app.logger.debug(u"GET MessageList %s" % request.path)

        user = get_user_or_error(username)

        if "start" in request.args:
            start = parse_datetime(request.args["start"])
        else:
            start = user.last_fetch

        if "end" in request.args:
            end = parse_datetime(request.args["end"])
            if "start" not in request.args:
                # If only "end" is specified, get all messages up to that time, not just the new ones
                start = BEGINNING_OF_TIME
        else:
            end = datetime.now(pytz.utc)

        app.logger.debug(u"Retrieving messages between %s and %s" % (start, end))
        app.logger.debug(u"Time span: %s" % (end - start))

        messages = Message.query.filter_by(receiver=user).filter(Message.timestamp.between(start, end)).all()

        app.logger.debug(u"Query returned %d messages" % len(messages))

        user.last_fetch = datetime.now(pytz.utc)
        db_session.commit()

        return [dictify_message(message) for message in messages]


api.add_resource(MessageResource, u"/<username>/message/<msg_id>/", u"/<username>/message/")
api.add_resource(MessageList, u"/<username>/messages/")


def setup_db():
    """
    Sets up the database, connections, etc.
    :return: a database session object that can be used to access the database
    """

    filename = app.config.get("DATABASE", "sqlite:////tmp/babbel.db")
    engine = create_engine(filename, convert_unicode=True)
    global db_session
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    Base.metadata.create_all(bind=engine)
    Base.query = db_session.query_property()

    testing = app.config.get("TESTING", False)
    if not testing:
        populate_db(db_session)

    return db_session


app.before_first_request(setup_db)

if __name__ == "__main__":
    app.run(debug=True)
