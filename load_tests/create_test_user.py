import requests
import json
from pathlib import Path


BASE_URL = "http://127.0.0.1:8000"

USERS_FILE = Path(__file__).parent / "load_test_users.json"

users = []

for i in range(1, 11):

    email = f"loadtest{i}@example.com"
    username = f"loadtest_user_{i}"
    password = "LoadTest@123"

    print(f"\nCreating User {i}...")

    # 1. Register
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )

    print("Register:", register_response.status_code)

    # If user already exists, we can still try to login
    if register_response.status_code not in [201, 400]:
        print(register_response.text)
        continue

    # 2. Login
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

    print("Login:", login_response.status_code)

    if login_response.status_code != 200:
        print(login_response.text)
        continue

    token = login_response.json()["acess_token"]

    # 3. Generate API key
    api_key_response = requests.post(
        f"{BASE_URL}/generate_api_key",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    print("API Key:", api_key_response.status_code)

    if api_key_response.status_code != 200:
        print(api_key_response.text)
        continue

    api_key = api_key_response.json()["api_key"]

    users.append({
        "username": username,
        "email": email,
        "token": token,
        "api_key": api_key
    })


# Save credentials in the same folder as this script
with open(USERS_FILE, "w") as file:
    json.dump(users, file, indent=4)

print("\n================================")
print(f"Created {len(users)} test users")
print(f"Credentials saved to {USERS_FILE}")
print("================================")