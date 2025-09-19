import boto3
import requests
import secrets
import os
import logging
import base64
from nacl.public import PublicKey, SealedBox

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PUBLIC_KEY_URL = os.environ['PUBLIC_KEY_URL']
UPDATE_SECRET_URL = os.environ['UPDATE_SECRET_URL']
PROBE_URL = os.environ['PROBE_URL']
API_KEY_ID = os.environ['API_KEY_ID']
TEST_CLIENT_ID = os.environ['TEST_CLIENT_ID']
TEST_AUDIENCE = os.environ['TEST_AUDIENCE']

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

def create_secret(token: str, arn: str) -> dict | None:
    try:
        _secrets.get_secret_value(SecretId=arn, VersionStage="AWSPENDING")
        return {'statusCode': 500, 'body': 'Pending secret already exists'}
    except _secrets.exceptions.ResourceNotFoundException:
        pass

    new_secret = secrets.token_urlsafe(32)

    _secrets.put_secret_value(
        SecretId = arn,
        ClientRequestToken = token,
        SecretString = new_secret,
        VersionStages = ['AWSPENDING']
    )

    logger.info("STEP: Create Secret Complete")

def set_secret(secret: str) -> None:
    public_key = get_public_key()
    secret = encrypt_secret(secret.encode(), public_key['secret'])

    body = {
        "id": "DISTRIBUTED_SECRET",
        "secret": secret,
        "key_id": public_key['key_id'],
        "domain": "*"
    }

    resp = requests.patch(UPDATE_SECRET_URL, headers=_base_header, json=body)
    resp.raise_for_status()

    logger.info("STEP: Set Secret Complete")


def test_secret(arn: str) -> dict:
    secret = _secrets.get_secret_value(SecretId=arn, VersionStage="AWSPENDING")['SecretString']
    body = {
        "client_id": TEST_CLIENT_ID,
        "audience": TEST_AUDIENCE
    }

    token_response = requests.post(
        PROBE_URL, 
        json=body,
        headers={"Content-Type": "application/json", "x-client-secret": secret}
    )
    token_response.raise_for_status()

    logger.info("STEP: Test Secret Complete")
    return {"message": "testSecret succeeded"}

def finish_secret(token: str, arn: str) -> dict:
    meta = _secrets.describe_secret(SecretId=arn)
    current_version = None
    for v, stages in meta['VersionIdsToStages'].items():
        if 'AWSCURRENT' in stages:
            current_version = v
            break
    
    _secrets.update_secret_version_stage(
        SecretId = arn,
        VersionStage = "AWSCURRENT",
        MoveToVersionId = token,
        RemoveFromVersionId = current_version
    )

    logger.info("STEP: Finish Secret Complete")
    return {"message": "finishSecret complete"}

def lambda_handler(event, context):
    step = event['Step']
    token = event['ClientRequestToken']
    arn = event.get('SecretId')

    if step == 'createSecret':
        return create_secret(token, arn)
    elif step == 'setSecret':
        return set_secret(_secrets.get_secret_value(SecretId=arn, VersionStage="AWSPENDING")['SecretString'])
    elif step == 'testSecret':
        return test_secret(arn)
    elif step == 'finishSecret':
        return finish_secret(token, arn)