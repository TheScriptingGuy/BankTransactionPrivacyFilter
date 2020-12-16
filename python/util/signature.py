import datetime
import uuid
import base64

from hashlib import sha256, sha512
from Crypto.Hash import SHA256, SHA512
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class RabobankSignature:
    def __init__(self, body, use_256=True):
        self.body = body
        self.use_256 = use_256
        self.headers = self._get_signing_headers()

    @property
    def value(self):
        return

    def _get_signing_headers(self):
        date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        request_id = str(uuid.uuid4())
        return {'date': date, 'digest': self._digest, 'x-request-id': request_id}

    @property
    def _digest(self):
        return Digest(self.body, self.use_256).value

    @property
    def _signature(self):
        return Signature(self.headers, self.use_256).value


class Digest:
    def __init__(self, body, use_256):
        self.body = body
        self.use_256 = use_256

    @property
    def value(self):
        output = base64.b64encode(self._hashed.digest())
        return self._prefix + output.decode('utf-8')

    @property
    def _hashed(self):
        to_hash = self.body.encode('utf-8')
        return sha256(to_hash) if self.use_256 else sha512(to_hash)

    @property
    def _prefix(self):
        return 'sha-256' if self.use_256 else 'sha-512'


class Signature:
    def __init__(self, headers, use_256):
        self.headers = headers
        self.use_256 = use_256
        self.value = self._get_signature()

    @property
    def signing_string(self):
        return '\n'.join([key + ': ' + self.headers[key] for key in self.headers.keys()]).encode('utf-8')

    def _get_signature(self):
        with open('certs/rabobank_key.pem', 'r') as f:
            private_key = RSA.import_key(f.read())
        hash_digest = SHA256.new(self.signing_string) if self.use_256 else SHA512.new(self.signing_string)
        signature = pkcs1_15.new(private_key).sign(hash_digest)
        return base64.b64encode(signature)


def build_signature(body, use_256=True):
    signing_headers, signature = get_hardcoded_signature(body)
    key_id = '1523433508'
    algorithm = 'rsa-sha256' if use_256 else 'rsa-sha512'
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


def create_digest(body, use_256=True):
    hashed = sha256(body.encode('utf-8')) if use_256 else sha512(body.encode('utf-8'))
    print(hashed.hexdigest())
    output = base64.b64encode(hashed.digest())
    prefix = 'sha-256=' if use_256 else 'sha-512='
    return prefix + output.decode('utf-8')


def create_signing_string(headers):
    return '\n'.join([key + ': ' + headers[key] for key in headers.keys()])


def sign_string(signing_string, use_256=True):
    with open('certs/rabobank_key.pem', 'r') as f:
        private_key = RSA.import_key(f.read())
    digest = SHA256.new(signing_string.encode('utf-8')) if use_256 else SHA512.new(signing_string.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(digest)
    return base64.b64encode(signature)
