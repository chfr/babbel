# coding=utf-8
from datetime import datetime, timedelta
from urllib import quote_plus

import pytz
from flask import escape, request, Blueprint, current_app

import babbel
from models import User, Message

views = Blueprint("views", __name__)

# Below is the ugly code for the "client".
# I've made no effort to make the client return valid HTML, or even make it fully functional as a messaging tool.
# It's the equivalent of a debug printout, pretty much.


@views.route("/dates/", methods=["GET"])
def dates():
    now = datetime.now(tz=pytz.utc)
    ret = "<html><body><table cellspacing=\"10\"><tr><td>When</td><td>Timestamp</td><td>URL encoded</td></tr>"

    minus5 = now + timedelta(minutes=-5)
    ret += "<tr><td>-5 min</td><td>%s</td><td>%s</td></tr>" % (minus5.isoformat(), quote_plus(minus5.isoformat()))

    minus1 = now + timedelta(minutes=-1)
    ret += "<tr><td>-1 min</td><td>%s</td><td>%s</td></tr>" % (minus1.isoformat(), quote_plus(minus1.isoformat()))

    ret += "<tr><td><b>now</b></td><td>%s</td><td>%s</td></tr>" % (now.isoformat(), quote_plus(now.isoformat()))

    plus1 = now + timedelta(minutes=1)
    ret += "<tr><td>+1 min</td><td>%s</td><td>%s</td></tr>" % (plus1.isoformat(), quote_plus(plus1.isoformat()))

    plus5 = now + timedelta(minutes=5)
    ret += "<tr><td>+5 min</td><td>%s</td><td>%s</td></tr>" % (plus5.isoformat(), quote_plus(plus5.isoformat()))

    ret += "</table></body></html>"

    return ret


@views.route("/<string:username>/", methods=["GET"])
def index(username):
    """
    Simple view that allows you to send messages and see all of your own messages.
    """
    current_app.logger.debug(u"GET index %s" % request.path)

    user = babbel.get_user_or_error(username)
    messages = Message.query.filter_by(receiver=user).order_by(Message.timestamp)
    messagestring = u"<br>".join(unicode(message) for message in messages)

    return u"""Logged in as: %s<br>
            <form action="/%s/message/" method="post">
                <p>Recipient:<input type=text name=receiver>
                <p>Message:<input type=text name=message>
                <p><input type=submit value=Send>
            </form>
            <p>%s</p>
        """ % (username, username, messagestring)


@views.route("/db/", methods=["GET"])
def db():
    """
    Displays the contents of the database (messages and users).
    """
    current_app.logger.debug(u"GET db %s" % request.path)

    users = User.query.all()
    num_users = User.query.count()
    userstring = u"<br>".join(escape(user) for user in users)
    messages = Message.query.all()
    num_messages = len(messages)
    messagestring = u"<br>".join(escape(message) for message in messages)

    return u"""
    users: %s<br>
    <pre>%s</pre>
    <br><br>
    messages: %s<br>
    %s""" % (num_users, userstring, num_messages, messagestring)
