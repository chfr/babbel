# Babbel
Swedish for babble, unsurprisingly.
This is a basic messaging app built with a simple REST API. It's also the first Flask app I've built, which may make it a bit rough around the edges.  

## Usage

### API
For all API calls, ``2XX`` responses indicate success and ``4XX`` responses indicate failure. Requests that do not return any data will return ``204 No Content``.
#### Retrieving messages
When retrieving messages, the response will always be one or more JSON objects describing a message. The JSON object contains the ID, the sender's username, the message contents and a timestamp.  
A user's messages can be retrieved at ``/username/message/`` and ``/username/messages/``.  
To retrieve new messages, issue a GET request to ``/username/messages/``. If there are no new messages, an empty JSON list is returned. If there are new messages, they will be returned in a JSON list. The messages that are returned have then been "seen" and will not be returned again.  
To retrieve a specific message by ID issue a GET request to ``/username/message/id/``.  
To retrieve messages that were received within a specific time interval, GET requests like this are used:  
``/username/messages?start=<start timestamp>&end=<end timestamp>``  
Timestamps must be provided in the ISO 8601 format, like ``2016-10-08T16:17:25.735955+00:00``. In order to use them as GET parameters, they must be URL encoded into ``2016-10-08T16%3A17%3A25.735955%2B00%3A00``. Since these formats can be tedious to work with by hand,  ``/dates/`` has some pre-formatted examples.  
Requests can omit either of the ``start`` or ``end`` parameters. If ``start`` is omitted, all messages up until the ``end`` date are returned. If the ``end`` parameter is omitted, all messages starting from ``start`` are returned.
#### Deleting messages
To delete a single message by ID, issue a DELETE request to ``/username/message/id/``.  
To delete messages in bulk, issue a DELETE request to ``/username/message/`` with a JSON body in the following format:  
``{"ids": [1, 2, 3, 4]}``  
The ``Content-Type: application/json`` header should be present in the request.
#### Sending messages
To send a message, issue a POST request to ``/username/message/``. The body of the request should be form encoded with two parameters, ``receiver`` and ``message``:  
``receiver=elonmusk&message=Cool+rockets,+man``  
### cURL examples
Sending a message:  
``curl -X POST http://example.com/user1/message/ --data "receiver=user2&message=Hi+how+are+you?"``  
Deleting messages 28, 29 and 30:  
``curl -LX DELETE http://example.com/user1/message/ --data "{\"ids\": [28,29,30]}"``  
Deleting message 18:  
``curl -ILX DELETE http://example.com/user1/message/18/``  
Getting all messages between 2016-10-05 10:23:29 and 2016-10-28 10:23:50:
``curl "http://example.com/user1/messages/?start=2016-10-05T10%3A23%3A29.000000%2B00%3A00&end=2016-10-28T10%3A23%3A50.828699%2B00%3A00"``
### Using the quick and dirty client


## Running
To run it, clone this repo and put it somewhere where your WSGI server of choice can find it, making sure to set up the permissions correctly.
I used uWSGI to host it on my Raspberry Pi 3, see below for details.

## Deployment
I host it using uWSGI, installed from pip:
``pip install uwsgi``  
Then launched as follows (port 8080):  
``uwsgi -s /tmp/uwsgi.sock --manage-script-name --http :8080 --mount /babbel=babbel:app --virtualenv /path/to/your/venv --stats 127.0.0.1:8081 --master --processes 4 --threads 2 --touch-reload /path/to/touchfile``  


