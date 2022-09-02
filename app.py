from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from flask_cors import cross_origin
import requests
import json
import os
from dotenv import load_dotenv

app = Flask(__name__, instance_relative_config=False)

application = app


@app.route('/', methods=['GET'])
def about():
    return "<h1 style='color:blue'>Welcome</h1>"


@app.route('/debug', methods=['POST'])
@cross_origin()
def debug():
    print("debug")
    return "debug"


@app.route('/messages', methods=['POST'])
@cross_origin()
def messages():
    args = request.form
    message = args.get('Body')
    user = User
    user.phone_number = args.get('From')
    rc = RasaRestClient(user)
    resp = rc.send_message(message)
    print(resp)
    response = MessagingResponse()
    response.message(str(resp[0]['text']))

    return str(response)


class User():
    phone_number = ""
    conversation_id = "3593b9d650a54d8a8093d247ed1e9cdc"


load_dotenv()
rasa_base_url = os.getenv('rasa_base_url')
rasa_user = os.getenv('rasa_user')
rasa_password = os.getenv('rasa_password')


class RasaRestClient():

    token = None

    def __init__(self, user):

        self.user = user

    def send_message(self, message):
        return self.__post(f'/api/conversations/{self.user.conversation_id}/messages',
                           data={"message": message})

    def __login(self):
        resp = requests.post(f'{rasa_base_url}/api/auth',
                             data=json.dumps({'username': rasa_user, 'password': rasa_password}),
                             headers={'Content-type': 'application/json'})
        if resp.ok and 'access_token' in resp.json():
            RasaRestClient.token = resp.json()['access_token']
        else:
            raise Exception('Failed authenticate to rasa')

    def __before_request(self, attempt):
        if attempt > 1:
            raise Exception('Request to rasa failed')
        if RasaRestClient.token is None or attempt == 1:
            self.__login()

    def __after_request(self, resp, url, attempt, method, data=None):
        if not resp.ok:
            if resp.status_code == 401:
                if method == 'post':
                    return self.__post(url, data, attempt + 1)
                else:
                    raise Exception(f"RasaRestClient doesn't support http method {method}")
            else:
                raise Exception('Request to rasa failed')
        return resp.json()

    def __post(self, url, data, attempt=0):
        self.__before_request(attempt)
        resp = requests.post(f'{rasa_base_url}{url}',
                             data=json.dumps(data),
                             headers={'Authorization': f'Bearer {RasaRestClient.token}'})
        return self.__after_request(resp, url, attempt, 'post', data)


if __name__ == "__main__":
    application.run()
