from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from flask_cors import cross_origin
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
import pickle
from datetime import date, datetime, time, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials


app = Flask(__name__, instance_relative_config=False)

application = app


scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
file_name = '/home/ubuntu/JOCChatbotMiddleman/jocchatbot-7fdc3c134776.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
client = gspread.authorize(creds)

sheet = client.open('JOC Chatbot Users').sheet1

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
    phone_number = args.get('From')
    phone_col = sheet.col_values(1)
    values = len(phone_col)
    if phone_number in phone_col:
        idx = phone_col.index(phone_number)
        last_active = sheet.cell(idx, 2).value
        if datetime.now() - datetime.strptime(last_active, "%Y/%m/%d %H:%M:%f") > timedelta(minutes=15):
            res = "Hey! Welcome to the Just One Chesed ChesedMatch ChatBot. \n" \
               "Please answer a few questions so we can help you the best we can." \
               " You can write 'start over' at any point to go back to the main menu. \n" \
               "Let's get started, select what country you are from from the options below:"
        else:
            rc = RasaRestClient(user)
            resp = rc.send_message(message)
            res = ''
            for r in range(len(resp)):
                res += resp[r]['text']
        sheet.update_cell(idx, 2, datetime.now())
    else:
        sheet.insert_row([phone_number, str(datetime.now())], values + 1)
        rc = RasaRestClient(user)
        resp = rc.send_message(message)
        res = ""
        for r in range(len(resp)):
            res += resp[r]['text']


    response = MessagingResponse()
    response.message(str(res))

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
