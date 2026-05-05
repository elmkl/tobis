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
        raise HTTPException(404, "unknown city")
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
            raise HTTPException(502, str(e))

    # L-AE = AeroBus
    lae_route = None
    for line in lines:
        if line["id"] == "L-AE":
            lae_route = line
            break
            
    if not lae_route:
        raise HTTPException(404, "L-AE not found in ALSA Agadir response")

    # read with utf-8 to prevent charmap errors (even tho this may be unnecessary, not arabic chars in the aerobus data)
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
            raise HTTPException(502, str(e))

@router.get("/{city}/timetable")
async def alsa_timetable(city: str):
    cfg = _city(city)
    async with _client(cfg["subdomain"]) as client:
        try:
            response = await client.post(f"/program{_QS}", content=_body(cfg["city_id"]))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(502, str(e))

@router.get("/{city}/track/{route_id}")
async def track_alsa_route(city: str, route_id: str):
    # only Agadir L-AE has static fallback data right now
    # this is fetched from: https://www.alsa.ma/en/navette-aeroport
    if city.lower() == "agadir" and route_id.upper() == "L-AE":
        file_path = DATA_DIR / "agadir_aerobus.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        departures = data["schedule"]["monday_to_friday"]["from_city"]
        stops = data["stops"]
        return track_estimated_schedule(departures, 50, stops)
    raise HTTPException(status_code=501, detail="Either buses are out of service or ALSA is not providing feedback, sorry")