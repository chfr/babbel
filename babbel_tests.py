import babbel
import unittest
import tempfile
import os
from models import User, Message
from datetime import datetime, timedelta
from urllib import quote_plus
import pytz
from flask import json

from babbel import setup_db


class BabbelTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.filename = tempfile.mkstemp()
        babbel.app.config["TESTING"] = True
        babbel.app.config["DATABASE"] = "sqlite:///%s" % self.filename
        # babbel.app.config["DEBUG"] = True
        babbel.app.logger.debug("Setting up temporary DB at %s" % self.filename)

        self.db_session = setup_db()
        self.app = babbel.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.filename)

    def create_user(self, username):
        with babbel.app.app_context():
            u = User(username)
            self.db_session.add(u)
            self.db_session.commit()

    def test_empty_db_404_errors(self):
        rv = self.app.get("/name/", follow_redirects=True)
        assert rv.status_code == 404

        rv = self.app.get("/name/message/0/", follow_redirects=True)
        assert rv.status_code == 404

        rv = self.app.get("/name/messages/", follow_redirects=True)
        assert rv.status_code == 404

        rv = self.app.delete("/name/message/0/", follow_redirects=True)
        assert rv.status_code == 404

        rv = self.app.delete("/name/message/", data={"ids": [0, 1]}, follow_redirects=True)
        assert rv.status_code == 404

        rv = self.app.post("/name/message/", data={"receiver": "me", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 404

    def test_user_page_returns_200(self):
        self.create_user("x")
        rv = self.app.get("/x/", follow_redirects=True)
        assert rv.status_code == 200

    def test_single_user_message_self(self):
        self.create_user("x")
        rv = self.app.post("/x/message/", data={"receiver": "x", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 204

        # Check that it shows up as a "new" message
        rv = self.app.get("/x/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that it doesn't show up as a "new" message anymore
        rv = self.app.get("/x/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" not in rv.data

    def test_two_users_messaging(self):
        self.create_user("x")
        self.create_user("y")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 204

        # Check that it shows up as a "new" message
        rv = self.app.get("/y/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that we can fetch it on its own
        rv = self.app.get("/y/message/1/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that it doesn't show up as a "new" message anymore
        rv = self.app.get("/y/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" not in rv.data

    def test_message_date_ranges(self):
        self.create_user("x")
        self.create_user("y")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        minus1 = now + timedelta(minutes=-1)
        plus1 = now + timedelta(minutes=1)
        plus5 = now + timedelta(minutes=5)

        # Check that it shows up between plus1 and minus1
        parameters = "?start=%s&end=%s" % (quote_plus(minus1.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that it doesn't show up between minus5 and minus1
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(minus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" not in rv.data

        # Check that it doesn't show up between plus1 and plus5
        parameters = "?start=%s&end=%s" % (quote_plus(plus1.isoformat()), quote_plus(plus5.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" not in rv.data

        # Check that it shows up when you only specify minus1 as the start date
        parameters = "?start=%s" % quote_plus(minus1.isoformat())
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that it shows up when you only specify plus1 as the end date
        parameters = "?end=%s" % quote_plus(plus1.isoformat())
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

    def test_delete_single_message(self):
        self.create_user("x")
        self.create_user("y")

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that it shows up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data

        # Delete the message and make sure it's not shown anymore
        rv = self.app.delete("/y/message/1/")
        assert rv.status_code == 204

        # Check that it does not up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" not in rv.data

        # Check that message 2 still exists
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 2!" in rv.data

    def test_delete_multiple_messages(self):
        self.create_user("x")
        self.create_user("y")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 3!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that both show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data
        assert "Test 2!" in rv.data

        # Delete the messages and make sure they're not shown anymore
        # For some reason you cannot specify data={"ids": [1, 2]}, so we turn it into JSON explicitly
        rv = self.app.delete("/y/message/", data=json.dumps({"ids": [1, 2]}), follow_redirects=True, headers={"Content-Type": "application/json"})
        assert rv.status_code == 204

        # Check that neither show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" not in rv.data
        assert "Test 2!" not in rv.data

        # Check that message 3 still exists
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 3!" in rv.data

    def test_delete_multiple_messages_combined_way(self):
        """
        DELETE requests to /username/message/<msg_id>/ also accept request bodies with message IDs, and both should be accepted.
        """
        self.create_user("x")
        self.create_user("y")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 3!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that both show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data
        assert "Test 2!" in rv.data

        # Delete the messages and make sure they're not shown anymore
        # For some reason you cannot specify data={"ids": [1, 2]}, so we turn it into JSON explicitly
        rv = self.app.delete("/y/message/1/", data=json.dumps({"ids": [2]}), follow_redirects=True, headers={"Content-Type": "application/json"})
        assert rv.status_code == 204

        # Check that neither show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" not in rv.data
        assert "Test 2!" not in rv.data

        # Check that message 3 still exists
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 3!" in rv.data

    def test_message_to_unknown_user(self):
        self.create_user("x")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 404

    def test_access_other_users_message(self):
        self.create_user("x")
        self.create_user("y")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test!"}, follow_redirects=True)
        assert rv.status_code == 204

        # Check that it shows up as a "new" message for y
        rv = self.app.get("/y/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" in rv.data

        # Check that it doesn't show up as a "new" message for x
        rv = self.app.get("/x/messages/", follow_redirects=True)
        assert rv.status_code == 200
        assert "Test!" not in rv.data

        # Check that we can't fetch it on its own
        rv = self.app.get("/x/message/1/", follow_redirects=True)
        assert rv.status_code == 404
        assert "Test!" not in rv.data

    def test_delete_other_users_message(self):
        self.create_user("x")
        self.create_user("y")

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that it shows up between plus1 and minus5 for y
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data

        # Try to delete y's message as x
        rv = self.app.delete("/x/message/1/")
        assert rv.status_code == 400

        # Check that it still shows up between plus1 and minus5 for y
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data

    def test_delete_multiple_messages_with_some_failing(self):
        self.create_user("x")
        self.create_user("y")
        self.create_user("z")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "z", "message": "Test 3!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that both show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data
        assert "Test 2!" in rv.data
        assert "Test 3!" not in rv.data

        # Delete the messages and make sure they're not shown anymore
        # For some reason you cannot specify data={"ids": [1, 2]}, so we turn it into JSON explicitly
        rv = self.app.delete("/y/message/", data=json.dumps({"ids": [1, 2, 3]}), follow_redirects=True, headers={"Content-Type": "application/json"})
        assert rv.status_code == 204

        # Check that neither show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" not in rv.data
        assert "Test 2!" not in rv.data

        # Check that message 3 still exists
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/z/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 3!" in rv.data

    def test_delete_multiple_messages_with_all_failing(self):
        self.create_user("x")
        self.create_user("y")
        self.create_user("z")
        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 1!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "y", "message": "Test 2!"}, follow_redirects=True)
        assert rv.status_code == 204

        rv = self.app.post("/x/message/", data={"receiver": "z", "message": "Test 3!"}, follow_redirects=True)
        assert rv.status_code == 204

        now = datetime.now(pytz.utc)
        minus5 = now + timedelta(minutes=-5)
        plus1 = now + timedelta(minutes=1)

        # Check that both show up for y between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data
        assert "Test 2!" in rv.data
        assert "Test 3!" not in rv.data

        # Check that message 3 shows up for z between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/z/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 3!" in rv.data

        # Try to delete z's message 3 as y
        # For some reason you cannot specify data={"ids": [1, 2]}, so we turn it into JSON explicitly
        rv = self.app.delete("/y/message/", data=json.dumps({"ids": [3]}), follow_redirects=True, headers={"Content-Type": "application/json"})
        assert rv.status_code == 400

        # Check that y's messages still show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/y/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 1!" in rv.data
        assert "Test 2!" in rv.data

        # Check that z's messages still show up between plus1 and minus5
        parameters = "?start=%s&end=%s" % (quote_plus(minus5.isoformat()), quote_plus(plus1.isoformat()))
        rv = self.app.get("/z/messages/%s" % parameters, follow_redirects=True)
        assert rv.status_code == 200
        assert "Test 3!" in rv.data


if __name__ == "__main__":
    unittest.main()
