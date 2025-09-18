import json
import boto3
import requests
import secrets
import os
import logging
import base64
from nacl.public import PublicKey, SealedBox

PUBLIC_KEY_URL = os.environ['PUBLIC_KEY_URL']
UPDATE_SECRET_URL = os.environ['UPDATE_SECRET_URL']
API_KEY_ID = os.environ['API_KEY_ID']
SHARED_SECRET_ID = os.environ['SHARED_SECRET_ID']

_secrets = boto3.client('secretsmanager')
_base_header = {
    'Content-Type': 'application/json',
    'x-api-key': _secrets.get_secret_value(SecretId=API_KEY_ID)['SecretString']
}

def get_public_key() -> dict:
    resp = requests.get(PUBLIC_KEY_URL, headers=_base_header)
    resp.raise_for_status()

    return resp.json()

def encrypt_secret(message: bytes, public_key_b64: str) -> str:
    raw_pub = base64.b64decode(public_key_b64, validate=True)
    sealed = SealedBox(PublicKey(raw_pub))
    ct = sealed.encrypt(message)

    return base64.b64encode(ct).decode()

def create_secret(token: str) -> dict | None:
    try:
        _secrets.get_secret_value(SecretId=SHARED_SECRET_ID, VersionStage="AWSPENDING")
        return {'statusCode': 500, 'body': 'Pending secret already exists'}
    except _secrets.exceptions.ResourceNotFoundException:
        pass

    new_secret = secrets.token_urlsafe(32)

    _secrets.put_secret_value(
        SecretId = SHARED_SECRET_ID,
        ClientRequestToken = token,
        SecretString = new_secret,
        VersionStages = ['AWSPENDING']
    )

def set_secret(encrytped_secret_b64: str) -> None:

    secret = encrypt_secret(b"" + encrytped_secret_b64.encode() + b"\n", get_public_key()['secret'])

    body = {
        "id": "DISTRIBUTED_SECRET",
        "secret": secret,
        "key_id": get_public_key()['key_id'],
        "domain": "*"
    }

    resp = requests.patch(UPDATE_SECRET_URL, headers=_base_header, json=body)
    resp.raise_for_status()


def test_secret():
    pass

def finish_secret():
    pass

def lambda_handler(event, context):
    # Create secret, set secret, test secret, finish secret
    step = event['step']
    token = event['ClientRequestToken']

    if step == 'createSecret':
        return create_secret(token)
    elif step == 'setSecret':
        return set_secret(_secrets.get_secret_value(SecretId=SHARED_SECRET_ID, VersionStage="AWSPENDING")['SecretString'])
    elif step == 'testSecret':
        return test_secret()
    elif step == 'finishSecret':
        return finish_secret()

    


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }