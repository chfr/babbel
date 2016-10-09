# Babbel
## The name
Swedish for babble, unsurprisingly.
## What?
This is a RESTful messaging app API built with Flask. It's also the first time I've used Flask, which might make it a bit rough around the edges.  

## Usage
The API can be used with utilities like cURL or (partially) via some simple views provided in this repository.  
There is a live version of this app hosted at http://chfr.net:8080 that should be open for business. It is hosted on a Raspberry Pi 3 on a residential fiber connection, so reliability can't be guaranteed.  
By default there are 3 users defined, ``a``, ``b`` and ``c``. So, as detailed in the descriptions below, the messages for user ``a`` can be accessed at http://chfr.net:8080/a/.

### API
For all API calls, ``2XX`` responses indicate success and ``4XX`` responses indicate failure. Requests that do not return any data will return ``204 No Content``.  
Some of the operations described below can be performed by the simple views available in the repository, but complete functionality can be achieved using cURL as described in the **cURL examples** section.
#### Retrieving messages
When retrieving messages, the response will always be one or more JSON objects describing a message. The JSON object contains the ID, the sender's username, the message contents and a timestamp.  
A user's messages can be retrieved at ``/username/message/`` and ``/username/messages/``.  
To retrieve new messages, issue a GET request to ``/username/messages/``. If there are no new messages, an empty JSON list is returned. If there are new messages, they will be returned in a JSON list. The messages that are returned have then been "seen" and will not be returned again in subsequent requests.  
To retrieve a specific message by ID, issue a GET request to ``/username/message/id/``.  
To retrieve messages that were received within a specific time interval, GET requests like this are used:  
``/username/messages/?start=<start timestamp>&end=<end timestamp>``  
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
Sending a message from user1 to user2:  
``curl -X POST http://example.com/user1/message/ --data "receiver=user2&message=Hi+how+are+you?"``  
Deleting messages 28, 29 and 30 as user1:  
``curl -LX DELETE http://example.com/user1/message/ --data "{\"ids\": [28,29,30]}"``  
Deleting message 18 as user1:  
``curl -ILX DELETE http://example.com/user1/message/18/``  
Getting all messages for user1 between 2016-10-05 10:23:29 and 2016-10-28 10:23:50:
``curl "http://example.com/user1/messages/?start=2016-10-05T10%3A23%3A29.000000%2B00%3A00&end=2016-10-28T10%3A23%3A50.828699%2B00%3A00"``
### Using the quick and dirty client
**Disclaimer**: This part of the code is untested, error prone and barely fit for use. It should not be used to judge the overall quality of the work.  
For convenience and debugging purposes, there are some views defined that can be used to see what's going on. At ``/db/`` there's a database dump of the users and messages that are stored in the database. At ``/username/`` there's a list of all the messages addressed to that user and a form that you can use to send messages. As mentioned earlier there's also ``/dates/`` that lists a couple of pre-formatted date strings to be used with the time interval filters for message retrieval.  
Not everything can be done through these views. Deletions, new message retrievals and time interval retrievals can only be done by calling the API directly.

## Running
To run it, clone this repo and put it somewhere where your WSGI server of choice can find it, making sure to set up the permissions correctly.  
In the directory where you cloned this repo, set up a virtualenv:  
``virtualenv venv``  
Note that this application is only tested using Python 2, so you may need to specify the Python interpreter as such:  
``virtualenv -p /path/to/python2 venv``  
Activate the virtual environment (command may differ depending on OS, this is for Ubuntu/Debian):  
``source venv/bin/activate``  
Install the required libraries using the following command:  
``pip install -r requirements.txt``  
I use uWSGI to host it on my Raspberry Pi 3, see below for details.  
I haven't tested it thoroughly, but running it with the built-in ``flask run`` command seems to work as well. To run with ``flask run``, remember to set the FLASK_APP environment variable:  
``export FLASK_APP=babbel.py``  


### Dependencies
The dependencies are listed in requirements.txt. Some notable inclusions:

* **Flask-RESTful**: Used to simplify the creation of RESTful API endpoints
* **SQLAlchemy**: Database ORM
* **Flask-SQLAlchemy**: Flask-specific bindings for SQLAlchemy
* **pytz**: Time zone library, helps to keep time zones in order

## Deployment
I host it using uWSGI, installed from pip:
``pip install uwsgi``  
Then launched as follows (port 8080):  
``uwsgi -s /tmp/uwsgi.sock --manage-script-name --http :8080 --mount /babbel=babbel:app --virtualenv /path/to/your/venv --stats 127.0.0.1:8081 --master --processes 4 --threads 2 --touch-reload /path/to/touchfile``  

## Known issues

* All timestamps are hardcoded to the UTC time zone. Different time zones should work but have not been tested at all.
* Trailing slashes are important when using cURL, even when using the -L switch to follow redirects.


