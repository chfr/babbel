# Babbel
Swedish for babble, unsurprisingly.
This is a basic messaging app built with a simple REST API. It's also the first Flask app I've built, which may make it a bit rough around the edges.  

## Usage


## API
 

## Running
To run it, clone this repo and put it somewhere where your WSGI server of choice can find it, making sure to set up the permissions correctly.
I used uWSGI to host it on my Raspberry Pi 3, see below for details. More to come in this section.

## Deployment
I host it using uWSGI, installed from pip:
``pip install uwsgi``
Then launched as follows (port 8080):
``uwsgi -s /tmp/uwsgi.sock --manage-script-name --http :8080 --mount /babbel=babbel:app --virtualenv /path/to/your/venv --stats 127.0.0.1:8081 --master --processes 4 --threads 2 --touch-reload /path/to/touchfile``

