#Correct code for webhook
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
import os
from dotenv import load_dotenv
# -----------------------------
# CONFIGURATION
# -----------------------------
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN") # replace with your token
ZOHO_FLOW_URL =  os.getenv("ZOHO_WEBHOOK_URL") # replace with your Zoho Flow URL
print("API_TOKEN from env:", os.getenv("API_TOKEN"))
# -----------------------------
# LOGGING SETUP
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("api_requests.log"), logging.StreamHandler()]
)

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="Secure Webhook API", description="API to safely forward requests to Zoho Flow")

# -----------------------------
# GET endpoint for testing
# -----------------------------
@app.get("/FinaurtAPI")
async def test_get():
    return {"message": "API is live. Use POST to send data securely."}

# -----------------------------
# POST endpoint for webhook integration
# -----------------------------
@app.post("/FinaurtAPI")
async def trigger_webhook(request: Request):
    # -----------------------------
    # 1. Check API token
    # -----------------------------
    token = request.headers.get("x-api-key")
    if token != API_TOKEN:
        logging.warning("Unauthorized token attempt")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API token")

    # -----------------------------
    # 2. Parse incoming request safely
    # -----------------------------
    try:
        # Try JSON first
        data = await request.json()
    except Exception:
        try:
            # Fallback to form-data
            form = await request.form()
            data = dict(form)
        except Exception as e:
            logging.error("Failed to parse request data: %s", e)
            raise HTTPException(status_code=400, detail="Invalid request data")

    logging.info("POST Webhook hit! Data: %s", data)

    # -----------------------------
    # 3. Forward data to Zoho Flow
    # -----------------------------
    try:
        async with httpx.AsyncClient() as client:
            # Use form data if received as form, otherwise JSON
            response = await client.post(ZOHO_FLOW_URL, data=data)
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
