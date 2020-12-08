import os
import base64
import json
import datetime
import uuid
from dotenv import load_dotenv
import http.client
from hashlib import sha256, sha512
from Crypto.Hash import SHA256, SHA512
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

load_dotenv()


USE_256 = False


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
    signing_headers, signature = get_hardcoded_signature(body)
    key_id = '1523433508'
    algorithm = 'rsa-sha256' if USE_256 else 'rsa-sha512'
    headers = 'date digest x-request-id'
    return signing_headers, f"keyId={key_id},algorithm={algorithm},headers={headers},signature={signature}"


def get_signature(body):
    digest = create_digest(body)
    headers = get_signing_headers(digest)
    signing_string = create_signing_string(headers)
    signature = sign_string(signing_string).decode('utf-8')
    return headers, signature


def get_hardcoded_signature(body):
    digest = create_digest(body)
    headers = {'date': 'Tue, 18 Sep 2018 09:51:01 GMT',
               'digest': digest,
               'x-request-id': '95126d8f-ae9d-4ac3-ac9e-c357dcd78811'}
    signing_string = create_signing_string(headers)
    signature = sign_string(signing_string).decode('utf-8')
    return headers, signature


def get_signing_headers(digest):
    date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    request_id = str(uuid.uuid4())
    return {'date': date, 'digest': digest, 'x-request-id': request_id}


def create_digest(body):
    hashed = sha256(body.encode('utf-8')) if USE_256 else sha512(body.encode('utf-8'))
    print(hashed.hexdigest())
    output = base64.b64encode(hashed.digest())
    prefix = 'sha-256=' if USE_256 else 'sha-512='
    return prefix + output.decode('utf-8')


def create_signing_string(headers):
    return '\n'.join([key + ': ' + headers[key] for key in headers.keys()])


def sign_string(signing_string):
    with open('python/certs/rabobank_key.pem', 'r') as f:
        private_key = RSA.import_key(f.read())
    digest = SHA256.new(signing_string.encode('utf-8')) if USE_256 else SHA512.new(signing_string.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(digest)
    return base64.b64encode(signature)


def get_tpp_certificate():
    return {
        'tpp-signature-certificate':
        "MIIDkDCCAnigAwIBAgIEWs3AJDANBgkqhkiG9w0BAQsFADCBiTELMAkGA1UEBhMCTkwx" +
        "EDAOBgNVBAgMB1V0cmVjaHQxEDAOBgNVBAcMB1V0cmVjaHQxETAPBgNVBAoMCFJhYm9i" +
        "YW5rMRwwGgYDVQQLDBNPbmxpbmUgVHJhbnNhY3Rpb25zMSUwIwYDVQQDDBxQU0QyIEFQ" +
        "SSBQSSBTZXJ2aWNlcyBTYW5kYm94MB4XDTE4MDQxMTA3NTgyOFoXDTIzMDQxMTA3NTgy" +
        "OFowgYkxCzAJBgNVBAYTAk5MMRAwDgYDVQQIDAdVdHJlY2h0MRAwDgYDVQQHDAdVdHJl" +
        "Y2h0MREwDwYDVQQKDAhSYWJvYmFuazEcMBoGA1UECwwTT25saW5lIFRyYW5zYWN0aW9u" +
        "czElMCMGA1UEAwwcUFNEMiBBUEkgUEkgU2VydmljZXMgU2FuZGJveDCCASIwDQYJKoZI" +
        "hvcNAQEBBQADggEPADCCAQoCggEBANoAjqGWUgCIm2F+0sBSEwLal+T3u+uldLikpxHC" +
        "B8iL1GD7FrRjcA+MVsxhvHly7vRsHK+tQyMSaeK782RHpY33qxPLc8LmoQLb2EuiQxXj" +
        "9POYkYBQ74qkrZnvKVlR3WoyQWeDOXnSY2wbNFfkP8ET4ElwyuIIEriwYhab0OIrnnrO" +
        "8X82/SPZxHwEd3aQjQ6uhiw8paDspJbS5WjEfuwY16KVVUYlhbtAwGjvc6aK0NBm+LH9" +
        "fMLpAE6gfGZNy0gzMDorVNbkQK1IoAGD8p9ZHdB0F3FwkILEjUiQW6nK+/fKDNJ0TBbp" +
        "gZUpY8bR460qzxKdeZ1yPDqX2Cjh6fkCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAYL4i" +
        "D6noMJAt63kDED4RB2mII/lssvHhcxuDpOm3Ims9urubFWEpvV5TgIBAxy9PBinOdjhO" +
        "1kGJJnYi7F1jv1qnZwTV1JhYbvxv3+vk0jaiu7Ew7G3ASlzruXyMhN6t6jk9MpaWGl5U" +
        "w1T+gNRUcWQRR44g3ahQRIS/UHkaV+vcpOa8j186/1X0ULHfbcVQk4LMmJeXqNs8sBAU" +
        "dKU/c6ssvj8jfJ4SfrurcBhY5UBTOdQOXTPY85aU3iFloerx7Oi9EHewxInOrU5XzqqT" +
        "z2AQPXezexVeAQxP27lzqCmYC7CFiam6QBr06VebkmnPLfs76n8CDc1cwE6gUl0rMA=="
    }
