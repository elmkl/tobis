import json
import pathlib
from fastapi import APIRouter, HTTPException
from models.journey import track_estimated_schedule

router = APIRouter(prefix="/urban/ifrane-aui", tags=["Urban"])
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

@router.get("/routes")
async def get_aui_routes():
    file_path = DATA_DIR / "al_akhawayn_university.json"
    if not file_path.exists():
        return {"count": 0, "routes": []}
        
    data = json.loads(file_path.read_text(encoding="utf-8"))
    
    routes = []
    for route in data.get("routes", []):
        routes.append({
            "id": route["id"], 
            "name": route.get("name", "")
        })
        
    return {"count": len(routes), "routes": routes}

@router.get("/track/{route_id}")
async def track_aui_route(route_id: str):
    file_path = DATA_DIR / "al_akhawayn_university.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Data missing")
        
    data = json.loads(file_path.read_text(encoding="utf-8"))
    selected_route = None
    
    for route in data.get("routes", []):
        if route["id"] == route_id:
            selected_route = route
            break
            
    if not selected_route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    outbound = selected_route.get("outbound", {})
    
    # Handle the weird naming they do for building 17
    departures = outbound.get("departures", [])
    if len(departures) == 0:
        departures = outbound.get("departures_b17", [])
        
    stops = []
    for stop in outbound.get("stops", []):
        stops.append(stop["name"])
    
    return track_estimated_schedule(departures, 25, stops)

@router.get("/schedule")
async def get_aui_schedule():
    file_path = DATA_DIR / "al_akhawayn_university.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return json.loads(file_path.read_text(encoding="utf-8"))