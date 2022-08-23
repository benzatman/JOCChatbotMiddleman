from flask import Flask

webhook_app = Flask('app')

# import the endpoint definitions from routes.py
from app import routes
