"""
Google OAuth + Gmail API helpers.
"""
from datetime import datetime, timedelta
import base64
import os
from email.mime.text import MIMEText

import requests


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send openid email profile"


def oauth_config():
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_OAUTH_REDIRECT_URI"),
    }


def config_ready():
    cfg = oauth_config()
    return bool(cfg["client_id"] and cfg["client_secret"] and cfg["redirect_uri"])


def build_auth_url(state):
    cfg = oauth_config()
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": GMAIL_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    req = requests.Request("GET", GOOGLE_AUTH_URL, params=params).prepare()
    return req.url


def exchange_code_for_tokens(code):
    cfg = oauth_config()
    data = {
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": cfg["redirect_uri"],
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    if not resp.ok:
        return None
    payload = resp.json()
    payload["expires_at"] = datetime.utcnow() + timedelta(seconds=int(payload.get("expires_in", 3600)))
    return payload


def refresh_access_token(refresh_token):
    cfg = oauth_config()
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    if not resp.ok:
        return None
    payload = resp.json()
    payload["expires_at"] = datetime.utcnow() + timedelta(seconds=int(payload.get("expires_in", 3600)))
    return payload


def fetch_google_email(access_token):
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if not resp.ok:
        return None
    return (resp.json() or {}).get("email")


def send_gmail_api(access_token, from_email, to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to_email
    msg["from"] = from_email
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    resp = requests.post(
        GMAIL_SEND_URL,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"raw": raw},
        timeout=20,
    )
    return resp.ok
