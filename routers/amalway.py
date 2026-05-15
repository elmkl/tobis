import json
import pathlib
from fastapi import APIRouter, HTTPException
from models.journey import track_estimated_schedule

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
router = APIRouter(prefix="/urban/amalway", tags=["Urban"])

@router.get("/routes")
async def amalway_routes():
    return {
        "routes": [
            {"id": "L1", "name": "Port - El Hajeb (BHNS)"}
        ]
    }

@router.get("/track/{route_id}")
async def track_amalway(route_id: str):
    if route_id.upper() != "L1":
        raise HTTPException(status_code=404, detail="invalid Amalway route")

    file_path = DATA_DIR / "amalway.json"
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load Amalway static data")
        
    stops = data["stops"]
    
    # 10 min frequency from 06:00 to 22:00
    departures = []
    for h in range(6, 23): # 6 to 22 inclusive
        for m in range(0, 60, 10):
            if h == 22 and m > 0: # after schedule, stop giving results
                break
            departures.append(f"{h:02d}:{m:02d}")
            
    # 45 mins end to end since it has a dedicated line
    result = track_estimated_schedule(departures, 45, stops)
    result["pricing"] = data["pricing"]
    result["operator"] = data["operator"]
    
    return result