import json
import boto3
import os
import time
import re
import base64
import hashlib
import jwt

_secrets = boto3.client('secretsmanager')
_cache = {}

SECRET_ID = os.environ['SHARED_SECRET_ID']
SIGNING_KEY_ID = os.environ['JWT_SIGNING_KEY_ID']
CLIENT_ID_REGEX = re.compile(os.environ['CLIENT_ID_REGEX'])

def resp(code: int, msg: str) -> dict:
    return {"statusCode": code, "body": json.dumps({"error": msg})}

def get_signing_key() -> str:
    if not _cache:
        _cache['SecretString'] = _secrets.get_secret_value(SecretID=SIGNING_KEY_ID)['SecretString']
    return _cache

def get_client_secret() -> list:
    current = _secrets.get_secret_value(SecretID=SECRET_ID, VersionStage="AWSCURRENT")['SecretString']
    previous = None

    try:
        previous = _secrets.get_secret_value(SecretID=SECRET_ID, VersionStage="AWSPREVIOUS")['SecretString']
    except _secrets.exceptions.ResourceNotFoundException:
        pass

    return [v for v in [current, previous] if v is not None]
    
def lambda_handler(event, context):
    body = json.loads(event.get('body','{}'))
    client_id = body.get('client_id')
    client_secret = body.get('client_secret')
    audience = body.get('audience')

    if audience != 'analytics-api': return resp(400, 'invalid_client')
    if not client_id or not CLIENT_ID_REGEX.fullmatch(client_id): return resp(400, 'invalid_client')
    if client_secret not in get_client_secret(): return resp(400, 'invalid_client')

    now = int(time.time())
    payload = {
        "iss": os.environ['TOKEN_ISSUER'],
        "sub": client_id,
        "aud": "analytics-api",
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, get_signing_key()['SecretString'], algorithm="HS256")
    return {"statusCode": 200, "body": json.dumps({"access_token": token, "token_type": "JWT", "expires_in": 3600})}