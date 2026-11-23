#!/usr/bin/env python
"""Terminal-only weather tools for ROS, powered by Open-Meteo."""
import argparse
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

CONFIG = Path.home() / ".config/rana-os/config.json"
console = Console()
RESET = "0"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight rain showers",
    81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def load_config():
    try:
        data = json.loads(CONFIG.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(data):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temp = CONFIG.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    temp.replace(CONFIG)


def request_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ROS-Terminal-Weather/1.0"}
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def get_device_location():
    """Use Termux:API only when installed and permitted; never open another app."""
    command = shutil.which("termux-location")
    if not command:
        return None
    try:
        result = subprocess.run(
            [command, "-p", "network", "-r", "once"],
            capture_output=True, text=True, timeout=12, check=True
        )
        data = json.loads(result.stdout)
        lat, lon = data.get("latitude"), data.get("longitude")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return None
    return None


def geocode(place):
    query = urllib.parse.urlencode({
        "name": place, "count": 1, "language": "en", "format": "json"
    })
    data = request_json("https://geocoding-api.open-meteo.com/v1/search?" + query)
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Location not found: {place}")
    item = results[0]
    label = ", ".join(x for x in (
        item.get("name"), item.get("admin1"), item.get("country")
    ) if x)
    return float(item["latitude"]), float(item["longitude"]), label


def resolve_location(args):
    if args and args[0].lower() not in ("auto", "default"):
        place = " ".join(args)
        lat, lon, label = geocode(place)
        return lat, lon, label

    if args and args[0].lower() == "auto":
        coords = get_device_location()
        if coords:
            return coords[0], coords[1], "Device location"

    config = load_config()
    place = config.get("weather_city", "Kolkata")
    lat, lon, label = geocode(place)
    return lat, lon, label


def fetch_weather(lat, lon, days=5):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,sunrise,sunset"
        ),
        "forecast_days": days,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    return request_json(url)


def condition(code):
    return WEATHER_CODES.get(int(code), "Unknown conditions")


def show_current(place, data):
    current = data["current"]
    color = load_config().get("color", "#bb66ff")
    temp = current.get("temperature_2m", "—")
    feels = current.get("apparent_temperature", "—")
    status = condition(current.get("weather_code", -1))
    humidity = current.get("relative_humidity_2m", "—")
    wind = current.get("wind_speed_10m", "—")
    rain = current.get("precipitation", "—")
    wind_dir = current.get("wind_direction_10m", "—")
    local_time = current.get("time", "").replace("T", " ")

    body = Table.grid(expand=True, padding=(0, 1))
    body.add_column(ratio=1)
    body.add_column(ratio=1)
    body.add_row(
        Text(f"{temp}°C", style=f"bold {color}", justify="center"),
        Text(status, style=f"bold {color}", justify="center")
    )
    body.add_row(
        Text(f"Feels like  {feels}°C", style="white", justify="center"),
        Text(f"Humidity  {humidity}%", style="white", justify="center")
    )
    body.add_row(
        Text(f"Wind  {wind} km/h · {wind_dir}°", style="white", justify="center"),
        Text(f"Precipitation  {rain} mm", style="white", justify="center")
    )
    console.print(Panel(
        Group(
            Text(place, style="white", justify="center"),
            body
        ),
        title=f"[bold {color}]ROS WEATHER[/]",
        subtitle=f"[{color} dim]Local time: {local_time}[/]",
        subtitle_align="center",
        border_style=color,
        expand=True
    ))


def show_forecast(data):
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    table = Table(
        title="5-DAY FORECAST",
        border_style=load_config().get("color", "#bb66ff"),
        expand=True
    )
    table.add_column("DATE", style="bold")
    table.add_column("CONDITION", overflow="fold")
    table.add_column("LOW", justify="right")
    table.add_column("HIGH", justify="right")
    table.add_column("RAIN", justify="right")
    for i, day in enumerate(dates):
        code = daily.get("weather_code", [0] * len(dates))[i]
        low = daily.get("temperature_2m_min", ["—"] * len(dates))[i]
        high = daily.get("temperature_2m_max", ["—"] * len(dates))[i]
        rain = daily.get("precipitation_probability_max", ["—"] * len(dates))[i]
        date_label = day[5:] if len(day) >= 10 else day
        table.add_row(date_label, condition(code), f"{low}°", f"{high}°", f"{rain}%")
    console.print(table)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ros weather",
        description="Show current weather and a 5-day forecast.",
        epilog=(
            "Examples:\n"
            "  ros weather Kolkata\n"
            "  ros weather --city Kolkata\n"
            "  ros weather -c New Delhi\n"
            "  ros weather auto\n"
            "  ros weather setcity Kolkata\n"
            "  ros weather --set-city New Delhi"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("location", nargs="*", metavar="CITY",
                        help="city name, or the legacy 'auto' / 'setcity CITY' syntax")
    parser.add_argument("-c", "--city", nargs="+", metavar="CITY",
                        help="city name (supports multiple words)")
    parser.add_argument("-a", "--auto", action="store_true",
                        help="try to use the device's location")
    parser.add_argument("--set-city", nargs="+", metavar="CITY",
                        help="save the default weather city")
    parser.add_argument("--forecast", action="store_true",
                        help="show only the 5-day forecast")
    return parser


def run(args=None, forecast_only=False):
    raw_args = list(args or [])
    parser = build_parser()
    if raw_args and raw_args[0].lower() == "help":
        parser.print_help()
        return
    parsed = parser.parse_args(raw_args)

    if parsed.auto and (parsed.city or parsed.location or parsed.set_city):
        parser.error("--auto cannot be combined with a city or --set-city")
    if parsed.city and parsed.location:
        parser.error("use either a CITY argument or --city, not both")
    if parsed.set_city and (parsed.city or parsed.location or parsed.auto):
        parser.error("--set-city cannot be combined with a weather location")
    if parsed.forecast and forecast_only:
        parser.error("--forecast is only needed with 'ros weather'")

    location_args = list(parsed.city or parsed.location)
    set_city = parsed.set_city

    # Preserve the original friendly command forms.
    if location_args and location_args[0].lower() == "setcity":
        if set_city:
            parser.error("default city was specified more than once")
        set_city = location_args[1:]
        location_args = []
    elif location_args == ["auto"]:
        parsed.auto = True
        location_args = []

    if parsed.auto:
        location_args = ["auto"]

    if set_city is not None:
        city = " ".join(set_city).strip()
        if not city:
            parser.error("--set-city requires a city name")
        try:
            geocode(city)
            config = load_config()
            config["weather_city"] = city
            save_config(config)
            console.print(f"[green]Default weather city saved: {city}[/]")
        except Exception as exc:
            console.print(f"[red]Could not save city: {exc}[/]")
        return

    try:
        lat, lon, place = resolve_location(location_args)
        data = fetch_weather(lat, lon, days=5)
        if not (forecast_only or parsed.forecast):
            show_current(place, data)
        show_forecast(data)
        console.print("[dim]Weather data: Open-Meteo · open-meteo.com[/]")
    except Exception as exc:
        console.print("[bold red]Weather unavailable[/]")
        console.print(f"[red]{exc}[/]")
        console.print("[dim]Check your internet connection or try another city.[/]")


if __name__ == "__main__":
    forecast = "--forecast" in sys.argv[1:]
    arguments = [x for x in sys.argv[1:] if x != "--forecast"]
    run(arguments, forecast_only=forecast)
