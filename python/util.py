import os
import base64
import json
import datetime
import uuid
from dotenv import load_dotenv
import http.client
from hashlib import sha256, sha512
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

load_dotenv()


def build_basic_auth():
    """
    Converts the CLIENT_ID and CLIENT_SECRET into a format that is requested
    by Rabobank's OAuth (Basic auth)
    """
    string = f'{os.getenv("CLIENT_ID")}:{os.getenv("CLIENT_SECRET")}'
    encoded_bytes = base64.b64encode(string.encode('utf-8'))
    return str(encoded_bytes, 'utf-8')


def get_access_code(authorization_code):
    """
    This method takes an authorization code and uses it to obtain an access code,
    which can be used to authorize later API request calls.
    """
    payload = f"grant_type=authorization_code&code={authorization_code}&redirect_uri={os.getenv('REDIRECT_URI')}"
    headers = {
        'authorization': f"Authorization: Basic {build_basic_auth()}",
        'content-type': "application/x-www-form-urlencoded",
        'accept': "application/json"
    }

    conn = http.client.HTTPSConnection(os.getenv('HOST'))
    conn.request("POST", "/openapi/sandbox/oauth2/token", payload, headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    return json.loads(data.decode('utf-8'))['access_token']


def build_signature(body):
    signature = get_signature(body)
    key_id = '1523433508'
    algorithm = 'rsa-sha512'
    headers = 'date digest x-request-id'
    return f"keyId={key_id},algorithm={algorithm},headers={headers},signature={signature}"


def get_signature(body):
    digest = create_digest(body)
    signing_string = create_signing_string(digest)
    signature = sign_string(signing_string)
    return signature


def create_digest(body):
    hashed = sha256(body.encode('utf-8'))
    output = base64.b64encode(hashed.digest())
    return 'sha256=' + output.decode('utf-8')


def create_signing_string(digest):
    date = datetime.datetime.now()
    request_id = uuid.uuid4()
    return f'date: {date}\n' \
           f'digest: {digest}\n' \
           f'x-request-id: {request_id}'


def sign_string(signing_string):
    with open('key.pem', 'r') as f:
        private_key = RSA.import_key(f.read())
    digest = SHA256.new(signing_string.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(digest)
    return base64.b64encode(signature)
