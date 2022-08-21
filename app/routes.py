from flask import request, jsonify
from app import webhook_app
from .rasa_rest_client import RasaRestClient

@webhook_app.route('/', methods=['Get'])
def about():
    return "<h1 style='color:blue'>Welcome</h1>"

@webhook_app.route('/messages/', methods=['POST'])
def messages():
        sms = request.values
        message = sms['data']
        user = sms['From']
        rc = RasaRestClient(user)
        response = rc.send_message(message)
        if 'buttons' in response[0]:
                response[0].pop('buttons')

        return jsonify(response)