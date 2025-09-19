import os
import requests
import random
import time
import sys

shared_secret = os.getenv("ClientSecret")
audience = os.getenv("Audience")
auth_url = os.getenv("AuthUrl")
api_url = os.getenv("ApiUrl")

def generate_client_id():
    base = "srv-prod-"
    suffix = os.urandom(5).hex()
    return base + suffix

def get_token(subject: str) -> str:
    auth_body = {
        "client_id": subject,
        "audience": audience
    }

    headers = {
        "x-client-secret": shared_secret,
        "Content-Type": "application/json"
    }

    print("Requesting token...")

    token_response = requests.post(
        auth_url,
        json=auth_body,
        headers=headers
    )
    token_response.raise_for_status()
    token = token_response.json()

    print("Token received:", token['access_token'][:10] + "...")

    return token['access_token']

def send_data(events: int):
    possible_values = {
        "device": ["pc", "mobile", "console"],
        "event_type": ["purchase", "level_up", "achievement", "join", "leave"],
        "player_id": [str(i) for i in range(100, 1000)],
        "item": ["sword", "shield", "potion", "truck", "car", "bike"],
        "player_server_duration": ["1200", "300", "600", "1800", "3600"]
    }

    subject = generate_client_id()
    token = get_token(subject)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Subject": subject
    }

    for i in range(events):
        event_body = {
            "device": random.choice(possible_values["device"]),
            "event_id": f"{subject}-00000{i+1:02d}",
            "event_type": random.choice(possible_values["event_type"]),
            "player_id": random.choice(possible_values["player_id"]),
            "server_id": subject,
            "server_version": "1.0.0",
            "ts": "2025-09-19T18:04:00Z",
            "properties": {
                "player_action": random.choice(possible_values["event_type"]),
                "item": random.choice(possible_values["item"]),
                "player_server_duration": random.choice(possible_values["player_server_duration"])
            }
        }

        print(f"Sending event {i+1}/{events}...")

        event_response = requests.post(
            api_url,
            headers=headers,
            json=event_body
        )
        event_response.raise_for_status()

        print(f"Event {i+1} sent, response:", event_response.status_code)

        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python load_generator.py <number_of_events>")
        sys.exit(1)

    try:
        num_events = int(sys.argv[1])
        if num_events <= 0:
            raise ValueError
    except ValueError:
        print("Please provide a positive integer for the number of events.")
        sys.exit(1)

    send_data(num_events)