import json
import os
import httpx
from app.config import get_settings

settings = get_settings()

async def fetch_weather_data(lat: float, lon: float):
    if settings.openweather_mode == "mock":
        # Baca dari file JSON statis
        mock_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_data", "sample_weather.json")
        try:
            with open(mock_file_path, "r") as f:
                data = json.load(f)
            
            # Update timestamps di mock data supaya selalu relevan dengan tanggal hari ini
            # Jadi risk engine tidak akan gagal mencari "overlap"
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            # Mulai dari jam 00:00 hari ini
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for i, item in enumerate(data.get("list", [])):
                # Buat jarak 3 jam untuk setiap entry (mirip OWM asli)
                new_time = start_dt + timedelta(hours=i*3)
                item["dt"] = int(new_time.timestamp())
                
            return data
        except Exception as e:
            raise ValueError(f"Gagal membaca mock data: {e}")
    else:
        # Panggil API asli OpenWeatherMap (5 Day / 3 Hour Forecast)
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={settings.openweather_api_key}&units=metric"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 401:
                raise ValueError("API Key OpenWeatherMap tidak valid (401).")
            elif response.status_code == 429:
                raise ValueError("Rate limit tercapai (429). Silakan coba beberapa saat lagi.")
            elif response.status_code != 200:
                raise ValueError(f"Gagal memanggil API OpenWeatherMap: {response.text}")
            return response.json()

async def geocode_location(location_name: str):
    if settings.openweather_mode == "mock":
        return {"lat": -6.2088, "lon": 106.8456} # Default to Jakarta for mock
        
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_name}&limit=1&appid={settings.openweather_api_key}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        if response.status_code == 401:
            raise ValueError("API Key OpenWeatherMap tidak valid (401).")
        elif response.status_code == 429:
            raise ValueError("Rate limit tercapai (429). Silakan coba beberapa saat lagi.")
        elif response.status_code != 200:
            raise ValueError(f"Gagal memanggil Geocoding API: {response.text}")
        data = response.json()
        if not data:
            return None
        return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
