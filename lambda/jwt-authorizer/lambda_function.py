import json
import boto3
import jwt
import os
import re
import logging
from jwt.exceptions import PyJWTError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_secrets = boto3.client('secretsmanager')
_signing_key = None

EXPECTED_AUDIENCE = os.environ['AUDIENCE']
EXPECTED_ISSUER = os.environ['ISSUER']
SIGNING_KEY_ID = os.environ['SIGNING_KEY_ID']
CLIENT_ID_REGEX = re.compile(os.environ['CLIENT_ID_REGEX'])

def get_signing_key() -> str:
    global _signing_key
    if _signing_key is None:
        _signing_key = _secrets.get_secret_value(SecretId=SIGNING_KEY_ID)['SecretString']
    
    return _signing_key

def deny(reason:str):
    logger.info(json.dumps({
        "event": "jwt_auth",
        "status": "denied",
        "reason": reason
    }))

    raise Exception("Unauthorized")

def validate_jwt(token: str, secret: str, subject: str) -> dict:
    claims = jwt.decode(
        token,
        secret,
        audience=EXPECTED_AUDIENCE,
        issuer=EXPECTED_ISSUER,
        leeway=5,
        options={
            "require": ["iss", "sub", "aud", "iat", "nbf", "exp"]
        },
        algorithms=["HS256"]
    )

    sub = claims.get("sub")
    if sub != subject or not CLIENT_ID_REGEX.fullmatch(sub):
        raise jwt.InvalidTokenError("invalid sub")
    
    return claims


def lambda_handler(event, context):
    token = event["headers"].get("Authorization")
    sub = event["headers"].get("X-Subject")
    
    if not token or not token.lower().startswith("bearer "):
        return deny("invalid_authorization_header")
    
    token = token[7:]

    try:
        claims = validate_jwt(token, get_signing_key(), sub)
    except PyJWTError as e:
        return deny(str(e))
    except Exception:
        return deny("invalid_token")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }