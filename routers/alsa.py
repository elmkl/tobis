import httpx
from fastapi import APIRouter, HTTPException
import json
import pathlib
from models.journey import track_estimated_schedule

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
router = APIRouter(prefix="/urban/alsa", tags=["Urban"])

CITIES = {
    "agadir":    {"subdomain": "agadir",    "city_id": 2},
    "khouribga": {"subdomain": "khouribga", "city_id": 4},
    "rabat":     {"subdomain": "rabat",     "city_id": 5},
    # TODO: Does alsa have more websites in secret?
}

# scraped from parameters on the network tab
_PORTLET = "com_babel_alsa_ma_portlet_ServiceInformationPortlet"
_QS = (
    f"?p_p_id={_PORTLET}"
    f"&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view"
    f"&p_p_resource_id=MarruecosGetLinesFromCityResourceCommand"
    f"&p_p_cacheability=cacheLevelPage"
)

def _client(subdomain):
    return httpx.AsyncClient(
        base_url=f"https://www.alsa.ma/{subdomain}",
        timeout=15,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

def _body(city_id):
    return f"_{_PORTLET}_cityId={city_id}"

def _city(name):
    cfg = CITIES.get(name.lower())
    if not cfg:
        raise HTTPException(status_code=404, detail="Unknown ALSA city")
    return cfg

@router.get("/cities")
async def alsa_cities():
    return list(CITIES.keys())

@router.get("/agadir/aerobus")
async def agadir_aerobus():
    cfg = CITIES["agadir"]
    async with _client(cfg["subdomain"]) as client:
        try:
            response = await client.post(f"/lignes{_QS}", content=_body(cfg["city_id"]))
            response.raise_for_status()
            lines = response.json().get("lines", [])
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

    # L-AE = shuttle for airport to city centre
    lae_route = None
    for line in lines:
        if line["id"] == "L-AE":
            lae_route = line
            break
            
    if not lae_route:
        raise HTTPException(status_code=404, detail="L-AE not found in ALSA Agadir response")

    file_path = DATA_DIR / "agadir_aerobus.json"
    static_data = json.loads(file_path.read_text(encoding="utf-8"))
    
    # enrich data with live entry and static data
    lae_route["price_MAD"] = static_data["price_MAD"]
    lae_route["price_roundtrip_MAD"] = static_data["price_roundtrip_MAD"]
    lae_route["airport_assistance"] = static_data["airport_assistance"]
    lae_route["schedule"] = static_data["schedule"]

    return lae_route

@router.get("/{city}/routes")
async def alsa_routes(city: str):
    cfg = _city(city)
    async with _client(cfg["subdomain"]) as client:
        try:
            response = await client.post(f"/lignes{_QS}", content=_body(cfg["city_id"]))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

@router.get("/{city}/timetable")
async def alsa_timetable(city: str):
    cfg = _city(city)
    async with _client(cfg["subdomain"]) as client:
        try:
            response = await client.post(f"/program{_QS}", content=_body(cfg["city_id"]))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

@router.get("/{city}/track/{route_id}")
async def track_alsa_route(city: str, route_id: str):
    if city.lower() == "agadir" and route_id.upper() == "L-AE":
        file_path = DATA_DIR / "agadir_aerobus.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        departures = data["schedule"]["monday_to_friday"]["from_city"]
        stops = data["stops"]
        return track_estimated_schedule(departures, 50, stops)
    
    # track estimated schedule with alsa
    cfg = _city(city)
    stops = []
    duration_min = 60 
    
    async with _client(cfg["subdomain"]) as client:
        try:
            response = await client.post(f"/lignes{_QS}", content=_body(cfg["city_id"]))
            response.raise_for_status()
            lines_data = response.json().get("lines", [])
            
            for line in lines_data:
                if line.get("id") == route_id:
                    if "stops" in line:
                        stops = line["stops"]
                    elif "name" in line:
                        route_name = line.get("name", "")
                        if " - " in route_name:
                            stops = route_name.split(" - ")
                        else:
                            stops = ["Terminus A", "Terminus B"]
                    break
                    
        except Exception as e:
            print(f"[ALSA] Failed to fetch route info for fallback: {e}")
            stops = [f"{city.capitalize()} Terminus A", f"{city.capitalize()} Terminus B"]

    if not stops:
        stops = [f"{route_id} Start", f"{route_id} End"]

    mocked_departures = []
    for hour in range(6, 23):
        hour_str = str(hour).zfill(2)
        mocked_departures.append(f"{hour_str}:00")
        mocked_departures.append(f"{hour_str}:30")

    return track_estimated_schedule(mocked_departures, duration_min, stops)