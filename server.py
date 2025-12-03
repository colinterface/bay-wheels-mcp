import asyncio
import httpx
import math
import os
import sys
import logging
from mcp.server.fastmcp import FastMCP
from geopy.distance import geodesic
from typing import Optional, List, Dict, Any

# Configure logging for container compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("bay-wheels")

GBFS_DISCOVERY_URL = "https://gbfs.baywheels.com/gbfs/2.3/gbfs.json"

async def get_feed_url(feed_name: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(GBFS_DISCOVERY_URL)
        data = response.json()
        feeds = data.get("data", {}).get("en", {}).get("feeds", [])
        for feed in feeds:
            if feed.get("name") == feed_name:
                return feed.get("url")
    raise ValueError(f"Feed {feed_name} not found")

async def fetch_feed(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

@mcp.tool()
async def find_nearest_bike(latitude: float, longitude: float, count: int = 1, bike_type: Optional[str] = None) -> str:
    """
    Find the nearest dock with at least N available bikes, or free bike locations if N=1.
    
    Args:
        latitude: The latitude of the search location.
        longitude: The longitude of the search location.
        count: The number of bikes needed (default 1).
        bike_type: Optional type of bike ('electric_bike' or 'classic_bike'). If None, any type.
    """
    try:
        station_info_url = await get_feed_url("station_information")
        station_status_url = await get_feed_url("station_status")
        free_bike_status_url = await get_feed_url("free_bike_status")

        # Fetch data concurrently
        station_info_data, station_status_data, free_bike_data = await asyncio.gather(
            fetch_feed(station_info_url),
            fetch_feed(station_status_url),
            fetch_feed(free_bike_status_url)
        )

        stations = {s["station_id"]: s for s in station_info_data["data"]["stations"]}
        statuses = {s["station_id"]: s for s in station_status_data["data"]["stations"]}
        free_bikes = free_bike_data["data"]["bikes"]

        candidates = []

        # Map user friendly names to vehicle_type_ids
        # 1: classic, 2: electric
        target_type_id = None
        if bike_type:
            if "electric" in bike_type.lower() or "ebike" in bike_type.lower():
                target_type_id = "2"
            elif "classic" in bike_type.lower() or "standard" in bike_type.lower():
                target_type_id = "1"

        # Check stations
        for station_id, station in stations.items():
            status = statuses.get(station_id)
            if not status or not status.get("is_renting"):
                continue

            available_count = 0
            if target_type_id:
                # Check specific vehicle types available
                if "vehicle_types_available" in status:
                    for v in status["vehicle_types_available"]:
                        if v.get("vehicle_type_id") == target_type_id:
                            available_count += v.get("count", 0)
            else:
                # Any bike
                available_count = status.get("num_bikes_available", 0)

            if available_count >= count:
                dist = geodesic((latitude, longitude), (station["lat"], station["lon"])).meters
                candidates.append({
                    "type": "Station",
                    "name": station["name"],
                    "distance": dist,
                    "available": available_count,
                    "lat": station["lat"],
                    "lon": station["lon"]
                })

        # Check free bikes (only if count is 1)
        if count == 1:
            for bike in free_bikes:
                if bike.get("is_reserved") or bike.get("is_disabled"):
                    continue
                
                # Filter by bike type if requested
                if target_type_id and bike.get("vehicle_type_id") != target_type_id:
                    continue
                
                dist = geodesic((latitude, longitude), (bike["lat"], bike["lon"])).meters
                candidates.append({
                    "type": "Free Bike",
                    "name": f"Free Bike ({bike.get('bike_id', 'unknown')})",
                    "distance": dist,
                    "available": 1,
                    "lat": bike["lat"],
                    "lon": bike["lon"]
                })

        if not candidates:
            return "No bikes found matching criteria."

        # Sort by distance
        candidates.sort(key=lambda x: x["distance"])
        nearest = candidates[0]

        return (f"Nearest option: {nearest['type']} - {nearest['name']}\n"
                f"Distance: {nearest['distance']:.1f} meters\n"
                f"Available: {nearest['available']}\n"
                f"Location: {nearest['lat']}, {nearest['lon']}")

    except Exception as e:
        return f"Error finding nearest bike: {str(e)}"

@mcp.tool()
async def find_nearest_dock_spaces(latitude: float, longitude: float, count: int = 1) -> str:
    """
    Find the nearest dock with at least N available return spaces.
    
    Args:
        latitude: The latitude of the search location.
        longitude: The longitude of the search location.
        count: The number of spaces needed (default 1).
    """
    try:
        station_info_url = await get_feed_url("station_information")
        station_status_url = await get_feed_url("station_status")

        station_info_data, station_status_data = await asyncio.gather(
            fetch_feed(station_info_url),
            fetch_feed(station_status_url)
        )

        stations = {s["station_id"]: s for s in station_info_data["data"]["stations"]}
        statuses = {s["station_id"]: s for s in station_status_data["data"]["stations"]}

        candidates = []

        for station_id, station in stations.items():
            status = statuses.get(station_id)
            if not status or not status.get("is_returning"):
                continue

            if status.get("num_docks_available", 0) >= count:
                dist = geodesic((latitude, longitude), (station["lat"], station["lon"])).meters
                candidates.append({
                    "name": station["name"],
                    "distance": dist,
                    "available": status["num_docks_available"],
                    "lat": station["lat"],
                    "lon": station["lon"]
                })

        if not candidates:
            return "No docks found with sufficient spaces."

        candidates.sort(key=lambda x: x["distance"])
        nearest = candidates[0]

        return (f"Nearest dock with spaces: {nearest['name']}\n"
                f"Distance: {nearest['distance']:.1f} meters\n"
                f"Spaces Available: {nearest['available']}\n"
                f"Location: {nearest['lat']}, {nearest['lon']}")

    except Exception as e:
        return f"Error finding nearest dock spaces: {str(e)}"

if __name__ == "__main__":
    # Support both stdio (local Claude Desktop) and streamable-http (deployed)
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    logger.info(f"Starting Bay Wheels MCP server with {transport} transport")
    mcp.run(transport=transport)
