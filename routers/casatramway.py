import json
import pathlib
import httpx
from fastapi import APIRouter, HTTPException
from models.journey import track_estimated_schedule

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
router = APIRouter(prefix="/urban/casatramway", tags=["Urban"])

@router.get("/route")
async def get_casatramway_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    url = "https://sim.105.prod.instant-system.com/fr/itineraire"
    payload = {
        "estimatedResults": "true",
        "from[latitude]": str(start_lat),
        "from[longitude]": str(start_lon),
        "to[latitude]": str(end_lat),
        "to[longitude]": str(end_lon),
        "modes[]": "TRAM", 
        "criterion": "FASTEST",
        "scholarLines": "EXCLUDE",
        "accessible": "false",
        "avoidDisruptions": "false"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.post(url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"[Casa Tramway] API Error: {str(e)}")

    try:
        trip_planner = data.get("response", {}).get("tripPlanner", {})
        journeys_raw = trip_planner.get("TRANSPORT", {}).get("groups", [])[0].get("results", {}).get("journeys", [])
    except (IndexError, AttributeError):
        return {"message": "No tram routes found.", "journeys": []}

    parsed_journeys = []
    for j in journeys_raw:
        stops = []
        for path in j.get("paths", []):
            if path.get("mode") == "TRAM":
                stops.append(path.get("start", {}).get("name", "Unknown"))
                for stop in path.get("stoppoints", []):
                    stops.append(stop.get("name", "Unknown"))
                stops.append(path.get("end", {}).get("name", "Unknown"))

        parsed_journeys.append({
            "lines": j.get("lines", []),
            "departure": j.get("realstartdatetime", "Unknown"),
            "arrival": j.get("arrivaldatetime", "Unknown"),
            "duration_minutes": j.get("totaltime", 0) // 60,
            "walk_distance_meters": j.get("totaldistancewalker", 0),
            "stops": stops
        })

    return {"status": "success", "route_count": len(parsed_journeys), "journeys": parsed_journeys}

@router.get("/search")
async def search_casatramway_stations(query: str):
    url = "https://sim.105.prod.instant-system.com/fr/lieux"
    payload = {"search": query, "limit": 10, "isWidget": "true"}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"[Casa Tramway] Search Error: {str(e)}")

    results = []
    for s in data.get("suggestions", []):
        if s.get("type") == "STOPAREA":
            results.append({
                "id": s.get("id"),
                "name_fr": s.get("name"),
                "city_ar": s.get("city"), 
                "full_label": s.get("value"),
                "lat": float(s.get("lat", 0)),
                "lon": float(s.get("lon", 0))
            })

    return {"query": query, "count": len(results), "results": results}


@router.get("/routes")
async def list_static_routes():
    file_path = DATA_DIR / "casatramway.json"
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return {"routes": [{"id": k, "name": f"Ligne {k}"} for k in data["lines"].keys()]}

@router.get("/track/{route_id}")
async def track_casatramway_static(route_id: str):
    route_id = route_id.upper()
    file_path = DATA_DIR / "casatramway.json"
    data = json.loads(file_path.read_text(encoding="utf-8"))
    
    if route_id not in data["lines"]:
        raise HTTPException(status_code=404, detail="Route not found")
    
    stops = data["lines"][route_id]
    ops = data["operating_hours"][route_id]
    
    # determine start hour and datetime for departures
    start_h, start_m = map(int, ops["start"].split(":"))
    end_h = int(ops["end"].split(":")[0])
    freq = ops["frequency_mins"]
    
    departures = []
    for h in range(start_h, end_h + 1):
        for m in range(0, 60, freq):
            if h == start_h and m < start_m: continue
            departures.append(f"{h:02d}:{m:02d}")
            
    result = track_estimated_schedule(departures, ops["duration_mins"], stops)
    result["operator"] = data["operator"]
    return result