from typing import Any
import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _weather_description(code: int | None) -> str:
    if code is None:
        return "Conditions unavailable"
    if code == 0:
        return "Clear"
    if code in (1, 2, 3):
        return "Mainly clear / partly cloudy"
    if code in (45, 48):
        return "Fog"
    if code in (51, 53, 55, 56, 57):
        return "Drizzle"
    if code in (61, 63, 65, 66, 67):
        return "Rain"
    if code in (71, 73, 75, 77):
        return "Snow / ice precipitation"
    if code in (80, 81, 82):
        return "Rain showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return "Variable conditions"


async def get_weather(location: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "ConstructionIntelligenceDemo/1.0"}) as client:
        geo_response = await client.get(GEOCODE_URL, params={"name": location, "count": 1, "language": "en", "format": "json"})
        geo_response.raise_for_status()
        places = geo_response.json().get("results") or []
        if not places:
            raise ValueError(f"No place could be found for '{location}'. Try a nearby city name.")
        place = places[0]
        response = await client.get(FORECAST_URL, params={
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,weather_code,wind_speed_10m,wind_gusts_10m",
            "daily": "precipitation_probability_max,weather_code,wind_speed_10m_max",
            "forecast_days": 1,
            "timezone": "auto",
        })
        response.raise_for_status()
        payload = response.json()
    current = payload.get("current", {})
    daily = payload.get("daily", {})
    code = current.get("weather_code")
    wind = current.get("wind_speed_10m")
    rain = current.get("precipitation", 0) or 0
    advice = []
    if code in (95, 96, 99):
        advice.append("Thunderstorm indicated: suspend exposed lifting and elevated work when site conditions or local alerts make it unsafe; follow the site's severe-weather plan.")
    if code in (61, 63, 65, 80, 81, 82) or rain > 0:
        advice.append("Rain/wet surfaces possible: inspect access routes, excavation stability, drainage, electrical protection, and concrete-placement conditions before work.")
    if isinstance(wind, (int, float)) and wind >= 30:
        advice.append("Strong wind: review crane, hoisting, scaffold, roof, and loose-material restrictions against manufacturer guidance and the site wind-action plan.")
    if not advice:
        advice.append("No severe condition is flagged by this simple rule set. Check local alerts and the site forecast before exposed or lifting work.")
    return {
        "location": ", ".join(part for part in [place.get("name"), place.get("admin1"), place.get("country")] if part),
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_kmh": wind,
        "wind_gust_kmh": current.get("wind_gusts_10m"),
        "precipitation_mm": rain,
        "condition": _weather_description(code),
        "weather_code": code,
        "precipitation_probability_max": (daily.get("precipitation_probability_max") or [None])[0],
        "forecast_high_wind_kmh": (daily.get("wind_speed_10m_max") or [None])[0],
        "timezone": payload.get("timezone", "local time"),
        "advisory": advice,
        "source": "Open-Meteo",
        "observed_at": current.get("time"),
    }
