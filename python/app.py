import os
import time
import shutil
import csv
import pandas as pd
import json
import io
import jsonpickle
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


@app.route('/filter')
def filter():
    #Get CSV File from ps2meniet for the latest data
    response = requests.request('GET',  "https://psd2meniet.nl/wp-content/uploads/2020/12/PSD2meniet-register-rekeningnummers-v20201204.csv")
    #decode unicode content in variable
    decoded_content = response.text
    
    #import CSV file into panda's dataframe
    AccountsToFiltersdf = pd.read_csv(io.StringIO(decoded_content), sep=';')

    #Import Json from file
    jsonfile = open('./input/input.json')
    jsonstring = jsonfile.read()
    #Get JSON input from post request
    jsonstring = request.data
    #Get CSV File from ps2meniet for the latest data
    response = requests.request('GET',  "https://psd2meniet.nl/wp-content/uploads/2020/12/PSD2meniet-register-rekeningnummers-v20201204.csv")
    #decode unicode content in variable
    decoded_content = response.text
    
    #import CSV file into panda's dataframe
    AccountsToFiltersdf = pd.read_csv(io.StringIO(decoded_content), sep=';')

    #Deserialize Json into Python Object
    jsonObject = jsonpickle.decode(jsonstring)
    #Get booked transactions
    bookedTransactions = ((jsonObject.get('transactions')).get('booked'))
    #Convert booked transactions list to panda's dataframe
    df = pd.DataFrame(bookedTransactions)
    #Convert Dictionary of DebtorAccount to Panda's series
    series1 = df.debtorAccount.apply(pd.Series)
    #Remove DebtorAccount Dictionary column and replace with the columns from the Panda's Series
    df = pd.concat([df.drop(['debtorAccount'], axis=1), df['debtorAccount'].apply(pd.Series)], axis=1)
    #Filter iban's based on the AccountsToFiltersdf
    filter = df['iban'].isin(AccountsToFiltersdf['IBANzonderBIC'])
    #Get index of ibans which are found
    indexArray = df[filter].index
    #Sort by descending indexes to delete list indexes in the correct sequence
    indexArray = indexArray.sort_values(ascending=False)
    #loop through the index of found values to delete list indices
    for index in indexArray:
        del(bookedTransactions[index])

    #Get Pendingtransactions
    pendingTransactions = ((jsonObject.get('transactions')).get('pending'))
    #Convert Pending transactions to panda's dataframe
    df = pd.DataFrame(pendingTransactions)
    #Convert Dictionary of CreditorAccount to Panda's series
    series1 = df.creditorAccount.apply(pd.Series)
    #Remove CreditorAccount Dictionary column and replace with the columns from the Panda's Series
    df = pd.concat([df.drop(['creditorAccount'], axis=1), df['creditorAccount'].apply(pd.Series)], axis=1)
    #Filter iban's based on the AccountsToFiltersdf
    filter = df['iban'].isin(AccountsToFiltersdf['IBANzonderBIC'])
    #Get index of ibans which are found
    indexArray = df[filter].index
    #Sort by descending indexes to delete list indexes in the correct sequence
    indexArray = indexArray.sort_values(ascending=False)

    #Serialize Python Object in JSON
    output = jsonpickle.encode(jsonObject)
    #Return json output
    return render_template('home.html', accounts=output)

@app.route('/apply-filter',methods=['POST'])
def applyfilter():
    #Get JSON input from post request
    jsonstring = request.data
    #Get CSV File from ps2meniet for the latest data
    response = requests.request('GET',  "https://psd2meniet.nl/wp-content/uploads/2020/12/PSD2meniet-register-rekeningnummers-v20201204.csv")
    #decode unicode content in variable
    decoded_content = response.text
    
    #import CSV file into panda's dataframe
    AccountsToFiltersdf = pd.read_csv(io.StringIO(decoded_content), sep=';')

    #Deserialize Json into Python Object
    jsonObject = jsonpickle.decode(jsonstring)
    #Get booked transactions
    bookedTransactions = ((jsonObject.get('transactions')).get('booked'))
    #Convert booked transactions list to panda's dataframe
    df = pd.DataFrame(bookedTransactions)
    #Convert Dictionary of DebtorAccount to Panda's series
    series1 = df.debtorAccount.apply(pd.Series)
    #Remove DebtorAccount Dictionary column and replace with the columns from the Panda's Series
    df = pd.concat([df.drop(['debtorAccount'], axis=1), df['debtorAccount'].apply(pd.Series)], axis=1)
    #Filter iban's based on the AccountsToFiltersdf
    filter = df['iban'].isin(AccountsToFiltersdf['IBANzonderBIC'])
    #Get index of ibans which are found
    indexArray = df[filter].index
    #Sort by descending indexes to delete list indexes in the correct sequence
    indexArray = indexArray.sort_values(ascending=False)
    #loop through the index of found values to delete list indices
    for index in indexArray:
        del(bookedTransactions[index])

    #Get Pendingtransactions
    pendingTransactions = ((jsonObject.get('transactions')).get('pending'))
    #Convert Pending transactions to panda's dataframe
    df = pd.DataFrame(pendingTransactions)
    #Convert Dictionary of CreditorAccount to Panda's series
    series1 = df.creditorAccount.apply(pd.Series)
    #Remove CreditorAccount Dictionary column and replace with the columns from the Panda's Series
    df = pd.concat([df.drop(['creditorAccount'], axis=1), df['creditorAccount'].apply(pd.Series)], axis=1)
    #Filter iban's based on the AccountsToFiltersdf
    filter = df['iban'].isin(AccountsToFiltersdf['IBANzonderBIC'])
    #Get index of ibans which are found
    indexArray = df[filter].index
    #Sort by descending indexes to delete list indexes in the correct sequence
    indexArray = indexArray.sort_values(ascending=False)

    #Serialize Python Object in JSON
    output = jsonpickle.encode(jsonObject)
    #Return json output
    return json.dumps(output)


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
    print(requests)
    print(headers)
    print(response.headers)
    print(response.content)
    return render_template('home.html', accounts=response.content)


if __name__ == '__main__':
    app.run(ssl_context=('certs/rabobank_cert.pem', 'certs/rabobank_key.pem'))
