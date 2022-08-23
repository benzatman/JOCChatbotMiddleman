from flask import Flask

webhook_app = Flask(__name__.split('.')[0])

# import the endpoint definitions from routes.py
from app import routes
