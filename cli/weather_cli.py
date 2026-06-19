import typer
import asyncio
import sys
import os
from rich.console import Console
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openweather_service import geocode_location, fetch_weather_data
from app.config import get_settings

app = typer.Typer()
console = Console()
settings = get_settings()

@app.command()
def check(city: str = typer.Option(..., "--city", help="City to fetch weather for")):
    """
    Fetch current weather forecast for a specific city.
    """
    console.print(f"[cyan]Fetching weather data for:[/cyan] [bold]{city}[/bold]")
    console.print(f"[dim]Mode: {settings.openweather_mode}[/dim]")
    
    async def run():
        coords = await geocode_location(city)
        if not coords:
            console.print(f"[red]City '{city}' not found.[/red]")
            return
            
        try:
            weather = await fetch_weather_data(coords["lat"], coords["lon"])
            if not weather or "list" not in weather:
                console.print("[red]Failed to get weather forecast.[/red]")
                return
                
            # Get the first forecast point
            current = weather["list"][0]
            
            table = Table(show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="bold")
            
            table.add_row("Temperature", f"{current['main']['temp']} °C")
            table.add_row("Humidity", f"{current['main']['humidity']} %")
            table.add_row("Rain Chance", f"{current.get('pop', 0) * 100} %")
            table.add_row("Wind Speed", f"{current['wind']['speed']} m/s")
            table.add_row("Cloud Coverage", f"{current['clouds']['all']} %")
            
            console.print("-----------------------------------")
            console.print(table)
            console.print("-----------------------------------")
            
            source = "OpenWeatherMap (live)" if weather.get("city", {}).get("name") != "Mock City" else "Mock Data"
            console.print(f"[green]Source:[/green] {source}")
            
        except Exception as e:
            console.print(f"[red]Error fetching weather: {e}[/red]")

    asyncio.run(run())

if __name__ == "__main__":
    app()
