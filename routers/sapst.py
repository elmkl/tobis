import json
import pathlib
import pytz
from datetime import datetime
from fastapi import APIRouter, HTTPException
from models.journey import track_exact_schedule

router = APIRouter(prefix="/urban/taghazout-bay", tags=["Urban"])
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

@router.get("/routes")
async def get_sapst_routes():
    file_path = DATA_DIR / "sapst_taghazout_bay.json"
    if not file_path.exists():
        return {"count": 0, "routes": []}
        
    data = json.loads(file_path.read_text(encoding="utf-8"))
    
    routes = []
    for route in data.get("routes", []):
        routes.append({
            "id": route["id"], 
            "name": f"{route.get('from')} -> {route.get('to')}"
        })
        
    return {"count": len(routes), "routes": routes}

@router.get("/schedule")
async def get_sapst_schedule():
    file_path = DATA_DIR / "sapst_taghazout_bay.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return json.loads(file_path.read_text(encoding="utf-8"))

@router.get("/track")
async def track_sapst_shuttle():
    file_path = DATA_DIR / "sapst_taghazout_bay.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Data file missing")
        
    data = json.loads(file_path.read_text(encoding="utf-8"))
    
    # map stop IDs to names so we will not return raw numbers to the frontend
    stop_names = {}
    for stop in data["stops"]:
        stop_names[stop["id"]] = stop["name"]
    
    current_time = datetime.now(pytz.timezone("Africa/Casablanca"))
    current_minutes = (current_time.hour * 60) + current_time.minute
    
    # we only have one route to worry about for now
    route = data["routes"][0] 
    active_passage = None
    
    # Find which bus loop is currently running based on the start and end times
    for passage in route["passages"]:
        schedule = passage["schedule"]
        
        start_time_parts = schedule[0]["time"].split(":")
        start_hour = int(start_time_parts[0])
        start_minute = int(start_time_parts[1])
        
        end_time_parts = schedule[-1]["time"].split(":")
        end_hour = int(end_time_parts[0])
        end_minute = int(end_time_parts[1])
        
        start_total_minutes = (start_hour * 60) + start_minute
        end_total_minutes = (end_hour * 60) + end_minute
        
        if start_total_minutes <= current_minutes <= end_total_minutes:
            active_passage = schedule
            break
            
    if not active_passage:
        return {"status": "no_active_bus", "progress": 0, "passed": None, "next": None}

    # Format the data how tracking function wants it
    formatted_schedule = []
    for stop in active_passage:
        formatted_schedule.append({
            "name": stop_names[stop["stop_id"]], 
            "time_str": stop["time"]
        })
    
    return track_exact_schedule(formatted_schedule)