# coding=utf-8
from datetime import datetime, timedelta
from urllib import quote_plus

import pytz
from flask import escape, request, Blueprint, current_app, render_template

import babbel
from models import User, Message

views = Blueprint("views", __name__)

# Below is the ugly code for the "client".
# I've made no effort to make the client return valid HTML, or even make it fully functional as a messaging tool.
# It's the equivalent of a debug printout, pretty much.


@views.route("/dates/", methods=["GET"])
def dates():
    now = datetime.now(tz=pytz.utc)

    minus5 = now + timedelta(minutes=-5)
    minus1 = now + timedelta(minutes=-1)
    plus1 = now + timedelta(minutes=1)
    plus5 = now + timedelta(minutes=5)

    return render_template("dates.html", minus5=minus5, minus1=minus1, now=now, plus1=plus1, plus5=plus5)


@views.route("/<string:username>/", methods=["GET"])
def index(username):
    """
    Simple view that allows you to send messages and see all of your own messages.
    """
    current_app.logger.debug(u"GET index %s" % request.path)

    user = babbel.get_user_or_error(username)
    messages = Message.query.filter_by(receiver=user).order_by(Message.timestamp)

    return render_template("profile.html", messages=messages, username=username)


@views.route("/db/", methods=["GET"])
def db():
    """
    Displays the contents of the database (messages and users).
    """
    current_app.logger.debug(u"GET db %s" % request.path)

    users = User.query.all()
    messages = Message.query.all()

    return render_template("db.html", users=users, messages=messages)
