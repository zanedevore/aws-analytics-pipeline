import json
import boto3
import jwt
import os
import re

_secrets = boto3.client('secretsmanager')
_signing_key = None

EXPECTED_AUDIENCE = os.environ['AUDIENCE']
EXPECTED_ISSUER = os.environ['ISSUER']
SIGNING_KEY_ID = os.environ['SIGNING_KEY_ID']
CLIENT_ID_REGEX = re.compile(os.environ['CLIENT_ID_REGEX'])

def get_signing_key():
    global _signing_key
    if _signing_key is None:
        _signing_key = _secrets.get_secret_value(SecretId=SIGNING_KEY_ID)['SecretString']
    
    return _signing_key

def validate_jwt(token: str, secret: str, subject: str) -> bool:
    try:
        claims = jwt.decode(
            token,
            secret,
            audience=EXPECTED_AUDIENCE,
            issuer=EXPECTED_ISSUER,
            leeway=5,
            options={"require": ["iss", "sub", "aud", "iat", "nbf", "exp"]},
            algorithms="HS256"
        )

        if claims.get("sub") != subject:
            raise jwt.InvalidTokenError("sub does not match")
        
        return True

    except Exception as e:
        return False

def lambda_handler(event, context):
    token = event["headers"].get("Authorization")
    sub = event["headers"].get("X-Subject")
    
    if not token:
        raise Exception("Unauthorized")
    
    token = token[7:] if token.lower().startswith("bearer") else token

    if not validate_jwt(token, get_signing_key(), sub):
        print("validation failed!")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }