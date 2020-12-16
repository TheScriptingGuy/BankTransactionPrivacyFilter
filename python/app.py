import os
import time

from flask import Flask, request, session, redirect, render_template
from dotenv import load_dotenv
import requests

from util.access_code import get_access_code
from util.headers import get_headers
from oauth import rabobank

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET')

BASE_URL = os.getenv('BASE_URL')


@app.route('/')
def hello_world():
    return render_template('home.html')


@app.route('/login')
def login():
    return rabobank.authorize(callback=os.getenv('REDIRECT_URI'))


@app.route('/authorization-code/callback')
def callback():
    authorization_code = request.args['code']

    # As specified by Rabobank's API: wait for their servers to be synchronised
    time.sleep(1)
    access_code = get_access_code(authorization_code)

    # Set the access code to the local storage (session)
    session['code'] = access_code
    return redirect('/')


@app.route('/accounts')
def accounts():
    try:
        access_code = session['code']
    except KeyError:
        return render_template('home.html', error='No Access Code given, login first.')

    headers = get_headers(access_code)
    response = requests.request('GET', f'{BASE_URL}/payments/account-information/ais/accounts',
                                headers=headers,
                                cert=('certs/rabobank_cert.pem', 'certs/rabobank_key.pem'))
    print(headers)
    print(response.headers)
    return render_template('home.html', accounts=response.content)


if __name__ == '__main__':
    app.run(ssl_context=('cert.pem', 'key.pem'))
