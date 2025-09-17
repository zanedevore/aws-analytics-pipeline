import json
import boto3
import os
import time
import re
import jwt
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_secrets = boto3.client('secretsmanager')
_signing_key = None

SECRET_ID = os.environ['SHARED_SECRET_ID']
SIGNING_KEY_ID = os.environ['SIGNING_KEY_ID']
CLIENT_ID_REGEX = re.compile(os.environ['CLIENT_ID_REGEX'])

def resp(code: int, msg: str, decision: str, client_id: str | None, request_id: str, source_ip: str) -> dict:
    logger.info(json.dumps({
        "event": "jwt_issue",
        "status": decision,
        "reason": msg,
        "client_id": client_id,
        "sourceIp": source_ip,
        "request_id": request_id
    }))
    return {"statusCode": code, "body": json.dumps({"error": 'invalid_client'})}

def get_client_secret() -> list[str]:
    current = _secrets.get_secret_value(SecretId=SECRET_ID, VersionStage="AWSCURRENT")['SecretString']
    previous = None

    try:
        previous = _secrets.get_secret_value(SecretId=SECRET_ID, VersionStage="AWSPREVIOUS")['SecretString']
    except _secrets.exceptions.ResourceNotFoundException:
        pass

    return [v for v in [current, previous] if v is not None]

def get_signing_key():
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
    
def lambda_handler(event, context):
    body = event.get('body', None)
    source_ip = get_source_ip(event)
    request_id = event.get('requestContext', {}).get('requestId', None)

    key = get_signing_key()

    if not body:
        return resp(400, 'invalid_request', 'rejected', None, request_id, source_ip)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return resp(400, 'invalid_request', 'rejected', None, request_id, source_ip)

    client_id = data.get('client_id', None)
    client_secret = data.get('client_secret', None)
    audience = data.get('audience', None)

    if audience != 'analytics-api': return resp(400, 'invalid_audience', 'rejected', client_id, request_id, source_ip)
    if not client_id or not CLIENT_ID_REGEX.fullmatch(client_id): return resp(400, 'invalid_client_id', 'rejected', client_id, request_id, source_ip)
    if client_secret not in get_client_secret(): return resp(400, 'invalid_client_secret', 'rejected', client_id, request_id, source_ip)

    now = int(time.time())
    payload = {
        "iss": os.environ['TOKEN_ISSUER'],
        "sub": client_id,
        "aud": "analytics-api",
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, key, algorithm="HS256")
    logger.info(json.dumps({
        "event": "jwt_issue",
        "status": 'approved',
        "reason": 'valid_client',
        "client_id": client_id,
        "sourceIp": source_ip,
        "request_id": request_id
    }))
    return {
        "statusCode": 200, 
        "body": json.dumps({
            "access_token": token, 
            "token_type": "JWT", 
            "expires_in": 3600
        })
    }