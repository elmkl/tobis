import asyncio
import pytz
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from data.cities import CITIES
from models.journey import Journey
from routers import alsa, casabus, ctm, sapst, supratours
from routers.ctm import search_ctm
from routers.supratours import search_supratours

# scaffolding
app = FastAPI(title="tobis", description="API for public transit in Morocco", version="0.1.0",)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],)

app.include_router(ctm.router)
app.include_router(supratours.router)
app.include_router(casabus.router)
app.include_router(alsa.router)
app.include_router(sapst.router)

_TZ = pytz.timezone("Africa/Casablanca")

def morocco_now():
    return datetime.now(_TZ).replace(tzinfo=None)

def tag_status(journey: Journey) -> Journey:
    now = morocco_now()
    dep = datetime.fromisoformat(journey.departure)
    arr = datetime.fromisoformat(journey.arrival)
    if now < dep:
        journey.status = "scheduled"
    elif dep <= now <= arr:
        journey.status = "running"
    else:
        journey.status = "arrived"
    return journey


# TODO: make a web portal for reviewer :D
@app.get("/")
async def root():
    return {"name": "tobis", "version": "0.1.0", "status": "ok"}

@app.get("/time")
async def current_time():
    now = datetime.now(_TZ)
    return {"time": now.strftime("%H:%M"), "datetime": now.isoformat(), "timezone": "Africa/Casablanca"}

@app.get("/cities")
async def list_cities():
    return {"count": len(CITIES), "cities": sorted(CITIES.keys())}

@app.get("/national/search", response_model=list[Journey])
async def search(
    from_city: str = Query(..., alias="from"),
    to_city: str = Query(..., alias="to"),
    travel_date: date = Query(default_factory=date.today),
):
    from_city = from_city.lower().strip()
    to_city = to_city.lower().strip()

    if from_city not in CITIES or to_city not in CITIES:
        raise HTTPException(status_code=400, detail="Unknown city. Please go to /cities endpoint a list of cities.")

    ctm_results, supra_results = await asyncio.gather(
        search_ctm(from_city, to_city, travel_date),
        search_supratours(from_city, to_city, travel_date),
    )

    results = [tag_status(j) for j in ctm_results + supra_results]
    results.sort(key=lambda j: j.departure)
    return results