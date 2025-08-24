import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for local development

import json
import jwt
from datetime import datetime, timedelta
import requests
from flask import Blueprint, redirect, request, jsonify, session
from oauthlib.oauth2 import WebApplicationClient
from models import users_db, create_user, get_user_by_email

# Load environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Local development redirect URI
DEV_REDIRECT_URL = "http://127.0.0.1:5000/google_login/callback"

# Blueprint
google_auth = Blueprint("google_auth", __name__)

# OAuth client
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Use the same JWT secret as api_routes
JWT_SECRET = os.environ.get("JWT_SECRET", "your-jwt-secret")

# ---------------- JWT helpers ----------------
def generate_jwt_token(user_data):
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'name': user_data['name'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ---------------- Routes ----------------
@google_auth.route("/google_login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=DEV_REDIRECT_URL,
        scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization code not found in request.", 400

    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=DEV_REDIRECT_URL,
        code=code
    )

    # Request tokens
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    userinfo = userinfo_response.json()

    if not userinfo.get("email_verified"):
        return "User email not available or not verified by Google.", 400

    users_email = userinfo["email"]
    users_name = userinfo.get("given_name", "")
    users_picture = userinfo.get("picture", "")

    # Get or create user
    user = get_user_by_email(users_email)
    if not user:
        user = create_user(users_name, users_email, users_picture)

    # Generate JWT token
    token = generate_jwt_token(user)

    # Store token in session
    session['jwt_token'] = token
    session['user'] = user

    # Redirect to frontend
    return redirect('/')

@google_auth.route("/api/auth/me")
def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = session.get('jwt_token')

    if not token:
        return jsonify({'error': 'No token provided'}), 401

    payload = verify_jwt_token(token)
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401

    user = get_user_by_email(payload['email'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user)

@google_auth.route("/api/auth/token")
def get_token():
    token = session.get('jwt_token')
    if not token:
        return jsonify({'error': 'No token found'}), 401
    return jsonify({'token': token})

@google_auth.route("/logout")
def logout():
    session.clear()
    return redirect('/')