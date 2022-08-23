from flask import Flask

webhook_app = Flask(__name__, instance_relative_config=False)

# import the endpoint definitions from routes.py
from app import routes
