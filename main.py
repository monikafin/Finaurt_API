from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import jwt
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv(find_dotenv())

API_SECRET = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("ZOHO_WEBHOOK_URL")  # Where we forward the form-data

if not API_SECRET:
    raise Exception("API_SECRET missing from .env")

app = FastAPI()


# -------------------------
# Generate JWT token (for testing)
# -------------------------
def generate_test_token():
    payload = {
        "user": "test_sender",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, API_SECRET, algorithm="HS256")
    return token


@app.get("/get-token")
def get_test_token():
    """Generate a test JWT token."""
    return {"token": generate_test_token()}


# -------------------------
# Verify the JWT token
# -------------------------
def verify_token(token: str):
    try:
        payload = jwt.decode(token, API_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# -------------------------
# Main Webhook Receiver (form-data)
# -------------------------
@app.post("/receive-webhook")
async def receive_webhook(request: Request):
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(401, "Authorization header missing")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Invalid Authorization format")

    token = auth_header.split(" ")[1]
    verify_token(token)

    # Read form-data
    try:
        form = await request.form()
        data = dict(form)
    except Exception as e:
        raise HTTPException(400, f"Invalid form-data: {str(e)}")

    # Forward to external webhook URL
    async with httpx.AsyncClient() as client:
        response = await client.post(WEBHOOK_URL, json=data)

    return {
        "message": "Webhook form-data processed successfully",
        "forward_status": response.status_code,
        "forward_response": response.text,
        "received_form_data": data
    }
