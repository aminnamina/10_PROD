import secrets
import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

app = FastAPI()

# CORS configuration
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database
url_db = {}  # Structure: {short_code: {long_url: str, clicks: int, created_at: datetime}}

# Pydantic models
class URLCreate(BaseModel):
    long_url: HttpUrl
    custom_code: str | None = None  # Optional custom short code

class URLResponse(BaseModel):
    short_url: str
    clicks: int

# Constants
LINK_EXPIRATION_DAYS = 7

@app.post("/api/shorten", response_model=URLResponse)
async def create_short_url(url_data: URLCreate, request: Request):
    """Creates a short URL with an optional custom code."""
    long_url = str(url_data.long_url)
    custom_code = url_data.custom_code

    if custom_code:
        # Validate custom code (e.g., alphanumeric, 4-10 characters)
        if not (4 <= len(custom_code) <= 10 and custom_code.isalnum()):
            raise HTTPException(status_code=400, detail="Custom code must be 4-10 alphanumeric characters")
        if custom_code in url_db:
            raise HTTPException(status_code=409, detail="Custom code already in use")
        short_code = custom_code
    else:
        # Generate random secure code
        short_code = secrets.token_urlsafe(6)
        while short_code in url_db:
            short_code = secrets.token_urlsafe(6)

    # Store URL with metadata
    url_db[short_code] = {
        "long_url": long_url,
        "clicks": 0,
        "created_at": datetime.datetime.utcnow()
    }

    # Form full short URL
    base_url = str(request.base_url).rstrip('/')
    short_url = f"{base_url}/{short_code}"

    return {"short_url": short_url, "clicks": 0}

@app.get("/{short_code}")
async def redirect_to_long_url(short_code: str):
    """Redirects to the long URL, increments clicks, and checks expiration."""
    entry = url_db.get(short_code)
    if not entry:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Check expiration
    created_at = entry["created_at"]
    expiration_date = created_at + datetime.timedelta(days=LINK_EXPIRATION_DAYS)
    if datetime.datetime.utcnow() > expiration_date:
        del url_db[short_code]  # Remove expired link
        raise HTTPException(status_code=404, detail="Short URL has expired")

    # Increment click count
    entry["clicks"] += 1

    return RedirectResponse(url=entry["long_url"])