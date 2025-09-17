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

def get_source_ip(event: dict) -> str | None:
    ip = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    if ip:
        return ip

    xff = (event.get("headers", {}) or {}).get("X-Forwarded-For") or (event.get("headers", {}) or {}).get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    return None

def deny(reason:str, source_ip: str, request_id: str) -> None:
    logger.info(json.dumps({
        "event": "jwt_auth",
        "status": "denied",
        "reason": reason,
        "source_ip": source_ip,
        "request_id": request_id
    }))

    raise Exception("Unauthorized")

def build_policy(principal_id: str, effect: str, resource: str) -> dict:
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": [resource]
                }
            ]
        }
    }
    return policy

def allow(sub: str, claims: dict, method_arn: str, source_ip: str, request_id: str) -> dict:
    logger.info(json.dumps({
        "event": "jwt_auth",
        "status": "allowed",
        "client_id": sub,
        "claims": claims,
        "source_ip": source_ip,
        "request_id": request_id
    }))

    return build_policy(sub, "Allow", method_arn)

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
    sourceIp = get_source_ip(event)
    request_id = event.get('requestContext', {}).get('requestId', None)

    token = event["headers"].get("Authorization")
    sub = event["headers"].get("X-Subject")
    
    if not token or not token.lower().startswith("bearer "):
        return deny("invalid_authorization_header", sourceIp, request_id)

    token = token[7:]

    try:
        claims = validate_jwt(token, get_signing_key(), sub)
    except PyJWTError as e:
        return deny(str(e), sourceIp, request_id)
    except Exception:
        return deny("invalid_token", sourceIp, request_id)

    return allow(claims["sub"], claims, event["methodArn"], sourceIp, request_id)