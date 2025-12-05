from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
import os
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

# -----------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------
load_dotenv()
ZOHO_FLOW_URL = os.getenv("ZOHO_WEBHOOK_URL")
SECRET_KEY = os.getenv("SECRET_KEY")  # internal only
ALGORITHM = "HS256"

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("api_requests.log"), logging.StreamHandler()]
)

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="Webhook API – No Token Required")

# -----------------------------
# INTERNAL JWT CREATION (for forwarding)
# -----------------------------
def create_internal_jwt(data: dict, expires_minutes: int = 60):
    """Generate JWT internally for forwarding or logging purposes"""
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = data.copy()
    payload.update({"exp": expire})
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# -----------------------------
# GET endpoint for testing
# -----------------------------
@app.get("/")
async def root():
    return {"message": "Server is live. POST to /FinaurtAPI to send data."}

# -----------------------------
# POST endpoint for webhook integration
# -----------------------------
@app.post("/FinaurtAPI")
async def trigger_webhook(request: Request):
    # -----------------------------
    # 1. Parse incoming request safely
    # -----------------------------
    try:
        data = await request.json()
    except:
        try:
            form = await request.form()
            data = dict(form)
        except Exception as e:
            logging.error("Failed to parse request: %s", e)
            raise HTTPException(status_code=400, detail="Invalid request data")

    logging.info("Webhook hit → Data: %s", data)

    # -----------------------------
    # 2. Generate internal JWT (optional, for forwarding or logs)
    # -----------------------------
    internal_token = create_internal_jwt({"internal": "forwarding"})

    # -----------------------------
    # 3. Forward data to Zoho Flow
    # -----------------------------
    try:
        headers = {"Authorization": f"Bearer {internal_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(ZOHO_FLOW_URL, headers=headers, data=data)
        logging.info("Forwarded to Zoho Flow. Status: %s, Response: %s", response.status_code, response.text)
    except Exception as e:
        logging.error("Failed to forward to Zoho Flow: %s", e)
        raise HTTPException(status_code=500, detail="Failed to forward to Zoho Flow")

    # -----------------------------
    # 4. Return response to client
    # -----------------------------
    return JSONResponse(
        status_code=200,
        content={
            "message": "POST request received and forwarded successfully",
            "received_data": data,
            "zoho_status": response.status_code,
            "zoho_response": response.text
        }
    )
