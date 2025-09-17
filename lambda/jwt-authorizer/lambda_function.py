import json
import jwt
import os

EXPECTED_AUDIENCE = os.environ['AUDIENCE']
EXPECTED_ISSUER = os.environ['ISSUER']

def validate_jwt(token: str, secret: str) -> dict: 
    claims = jwt.decode(
        token,
        secret,
        audience=EXPECTED_AUDIENCE,
        issuer=EXPECTED_ISSUER,
        leeway=5,
        options={"require": ["iss", "sub", "aud", "iat", "nbf", "exp"]},
        algorithms="HS256"
    )

def lambda_handler(event, context):
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }