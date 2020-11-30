import os

from dotenv import load_dotenv
from flask_oauth import OAuth

load_dotenv()

oauth = OAuth()
base_url = f'{os.getenv("BASE_URL")}/oauth2'

# flask_oauth configuration of Rabobank's OAuth
rabobank = oauth.remote_app(
    'rabobank2',
    base_url=base_url,
    request_token_url=None,
    access_token_url=f"{base_url}/token",
    authorize_url=f"{base_url}/authorize",
    consumer_key=os.getenv('CLIENT_ID'),
    consumer_secret=os.getenv('CLIENT_SECRET'),
    request_token_params={'scope': 'ais.balances.read ais.transactions.read-90days'},
)
