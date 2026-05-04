import httpx
from fastapi import APIRouter, HTTPException
 
router = APIRouter(prefix="/operators/casabus", tags=["ALSA Casablanca"])
http = httpx.AsyncClient(timeout=15)
 
 
@router.get("/routes")
async def casabus_routes():
    try:
        r = await http.post("https://api.alsaalbaida.ma/api/Routes/busList", json={"keyword": ""})
        r.raise_for_status()
        data = r.json()["data"]["busList"]
        return {"count": len(data), "routes": data}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
 
 
@router.get("/routes/{route_id}")
async def casabus_route_detail(route_id: str, switched: bool = False):
    # TODO: does this have gps data?
    try:
        r = await http.post(
            "https://api.alsaalbaida.ma/api/Routes/routedetail",
            json={"routeId": route_id, "isSwitched": switched},
        )
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))