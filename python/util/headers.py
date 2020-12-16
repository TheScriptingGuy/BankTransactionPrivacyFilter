import os

from util.signature import RabobankSignature
from util.tpp_signature import get_tpp_certificate


def get_headers(access_code):
    signature = RabobankSignature(body='', use_256=True)

    headers = {'x-ibm-client-id': os.getenv('CLIENT_ID'),
               'Authorization': 'Bearer ' + access_code,
               'signature': signature.value}
    headers.update(signature.headers)
    headers.update(get_tpp_certificate())
    return headers
