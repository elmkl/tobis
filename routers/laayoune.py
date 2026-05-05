import json
import pathlib
from fastapi import APIRouter, HTTPException
from models.journey import track_estimated_schedule

router = APIRouter(prefix="/urban/laayoune", tags=["Urban"])
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

def get_laayoune_data():
    file_path = DATA_DIR / "laayoune_bus.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="laayoune_bus.json not found")
    return json.loads(file_path.read_text(encoding="utf-8"))

@router.get("/routes")
async def get_routes():
    data = get_laayoune_data()
    return {"count": len(data["lines"]), "routes": data["lines"]}

@router.get("/routes/{route_id}")
async def get_route_detail(route_id: str):
    data = get_laayoune_data()
    for line in data["lines"]:
        if line["id"].upper() == route_id.upper():
            return line
    raise HTTPException(status_code=404, detail="Line not found")

@router.get("/schedule")
async def get_schedule():
    return get_laayoune_data()

@router.get("/track/{route_id}")
async def track_bus(route_id: str):
    data = get_laayoune_data()
    selected_line = None
    
    # find the requested line
    for line in data["lines"]:
        if line["id"].upper() == route_id.upper():
            selected_line = line
            break
            
    if not selected_line:
        raise HTTPException(status_code=404, detail="Line not found")
        
    duration = selected_line.get("duration_min")
    if not duration:
        duration = 60 # default to 60 mins if missing
        
    stops = selected_line.get("stops", [])
    
    # Due to a lack of data, adding a bus every hour on the dot and on the half hour
    departures = []
    for hour in range(6, 23): # from 6 AM to 10 PM
        hour_string = str(hour).zfill(2)
        departures.append(f"{hour_string}:00")
        departures.append(f"{hour_string}:30")
        
    return track_estimated_schedule(departures, duration, stops)