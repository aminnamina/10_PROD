import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
print(f"Loaded API_KEY: {API_KEY}")  # Debug print to verify key
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

class Coords(BaseModel):
    lat: float
    lon: float

@app.get("/api/weather/{city}")
async def get_weather(city: str):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key is not configured")
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WEATHER_BASE_URL, params=params)
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid OpenWeatherMap API key")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="City not found")
    if response.status_code != 200:
        error_detail = response.json().get("message", "Error fetching weather data")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    data = response.json()
    return {
        "city_name": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"]
    }

@app.get("/api/forecast/{city}")
async def get_forecast(city: str):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key is not configured")
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_BASE_URL, params=params)
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid OpenWeatherMap API key")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="City not found")
    if response.status_code != 200:
        error_detail = response.json().get("message", "Error fetching forecast data")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    data = response.json()
    forecast_list = []
    for entry in data["list"]:
        if "12:00:00" in entry["dt_txt"]:
            forecast_list.append({
                "date": entry["dt_txt"],
                "temperature": entry["main"]["temp"],
                "description": entry["weather"][0]["description"],
                "icon": entry["weather"][0]["icon"]
            })
    return {
        "city_name": data["city"]["name"],
        "forecast": forecast_list[:5]
    }

@app.post("/api/weather/coords")
async def get_weather_by_coords(coords: Coords):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key is not configured")
    params = {
        "lat": coords.lat,
        "lon": coords.lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WEATHER_BASE_URL, params=params)
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid OpenWeatherMap API key")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Location not found")
    if response.status_code != 200:
        error_detail = response.json().get("message", "Error fetching weather data")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    data = response.json()
    return {
        "city_name": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"]
    }