import requests
import json
import os
import time
import datetime

AUTH_URL = "https://cloud-identity.uitiot.vn/v3/auth/tokens"
TOKEN_FILE = "token.json"

auth_data = {
    "auth": {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": "23521518",
                    "domain": {"id": "default"},
                    "password": "HUI3fBTDLZpIish57Hw6"
                }
            }
        },
        "scope": {
            "project": {
                "name": "NT533.Q13-TH1.06",
                "domain": {"name": "Default"}
            }
        }
    }
}

def get_token_and_catalog():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            if time.time() < data["expires_at"]:
                print("🔁 Dùng lại token cũ.")
                # Gọi lại catalog để có danh sách service
                response = requests.post(AUTH_URL, json=auth_data)
                body = response.json()
                return data["token"], body

    print("🔑 Yêu cầu token mới...")
    response = requests.post(AUTH_URL, json=auth_data)
    if response.status_code != 201:
        raise Exception(f"❌ Lỗi xác thực: {response.status_code} {response.text}")

    token = response.headers["X-Subject-Token"]
    body = response.json()

    expires = body["token"]["expires_at"]
    exp_ts = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00")).timestamp()

    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token, "expires_at": exp_ts}, f)

    print("✅ Token mới:", token)
    return token, body


def get_endpoint(catalog, service_type, interface="public"):
    for service in catalog:
        if service["type"] == service_type:
            for ep in service.get("endpoints", []):
                if ep["interface"] == interface:
                    return ep["url"]
    return None