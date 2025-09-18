import os
import requests
import json

# Env variables
subject = os.getenv("Subject")
shared_secret = os.getenv("ClientSecret")
audience = os.getenv("Audience")
auth_url = os.getenv("AuthUrl")
api_url = os.getenv("ApiUrl")

# Get JWT token
auth_body = {
    "client_id": subject,
    "audience": audience
}

Headers = {
    "x-client-secret": shared_secret,
    "Content-Type": "application/json"
}

token_response = requests.post(
    auth_url,
    json=auth_body,
    headers=Headers
)
token_response.raise_for_status()
token = token_response.json()

# Send event
headers = {
    "Authorization": f"Bearer {token['access_token']}",
    "X-Subject": subject
}

event_body = {
    "event_type": "join",
    "player_id": "123",
    "server_id": subject,
    "ts": "2025-09-12T18:04:00Z"
}

event_response = requests.post(
    api_url,
    headers=headers,
    json=event_body
)
event_response.raise_for_status()

print("Event sent successfully:", event_response.json())
