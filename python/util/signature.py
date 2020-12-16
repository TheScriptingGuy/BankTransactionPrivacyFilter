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
        self.value = self._build_signature()

    def _get_signing_headers(self):
        date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        request_id = str(uuid.uuid4())
        return {'date': date, 'digest': self._digest, 'x-request-id': request_id}

    @property
    def hardcoded_headers(self):
        return {'date': 'Tue, 18 Sep 2018 09:51:01 GMT',
                'digest': self._digest,
                'x-request-id': '95126d8f-ae9d-4ac3-ac9e-c357dcd78811'}

    @property
    def _digest(self):
        return Digest(self.body, self.use_256).value

    @property
    def _signature(self):
        return Signature(self.headers, self.use_256).value

    def _build_signature(self):
        key_id = '1523433508'
        algorithm = 'rsa-sha256' if self.use_256 else 'rsa-sha512'
        headers = 'date digest x-request-id'
        return f"keyId={key_id},algorithm={algorithm},headers={headers},signature={self._signature}"


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
        return 'sha-256=' if self.use_256 else 'sha-512='


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
        return base64.b64encode(signature).decode('utf-8')
