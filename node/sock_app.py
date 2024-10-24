from flask_sock import Sock

from flask_app import flask_app

sock_app = Sock(flask_app)
