import json
import jwt
import os
import re

EXPECTED_AUDIENCE = os.environ['AUDIENCE']
EXPECTED_ISSUER = os.environ['ISSUER']
CLIENT_ID_REGEX = re.compile(os.environ['CLIENT_ID_REGEX'])

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
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }