import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/operators/alsa", tags=["ALSA"])

CITIES = {
    "agadir":    {"subdomain": "agadir", "city_id": 2},
    "khouribga": {"subdomain": "khouribga", "city_id": 4},
    "rabat":     {"subdomain": "rabat", "city_id": 5},
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
        raise HTTPException(404, f"unknown city, please try the following cities: {list(CITIES)}")
    return cfg

@router.get("/cities")
async def alsa_cities():
    return list(CITIES.keys())

@router.get("/{city}/routes")
async def alsa_routes(city: str):
    cfg = _city(city)
    async with _client(cfg["subdomain"]) as c:
        try:
            r = await c.post(f"/lignes{_QS}", content=_body(cfg["city_id"]))
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(502, str(e))

@router.get("/{city}/timetable")
async def alsa_timetable(city: str):
    cfg = _city(city)
    async with _client(cfg["subdomain"]) as c:
        try:
            r = await c.post(f"/program{_QS}", content=_body(cfg["city_id"]))
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(502, str(e))