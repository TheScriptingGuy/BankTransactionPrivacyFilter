import os
import base64
import http.client
import json


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