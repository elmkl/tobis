import asyncio
from datetime import date
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

# TODO: add more routers
app.include_router(ctm.router)
app.include_router(supratours.router)
app.include_router(casabus.router)
app.include_router(alsa.router)
app.include_router(sapst.router)

# TODO: make a web portal for reviewer :D
@app.get("/")
async def root():
    return {"name": "tobis", "version": "0.1.0", "status": "ok"}

@app.get("/cities")
async def list_cities():
    return {"count": len(CITIES), "cities": sorted(CITIES.keys())}

# search national providers
@app.get("/national/search", response_model=list[Journey])
async def search(from_city: str = Query(..., alias="from"), 
                to_city: str = Query(..., alias="to"),
                travel_date: date = Query(default_factory=date.today),):
    # normalize city names
    from_city = from_city.lower().strip()
    to_city = to_city.lower().strip()
 
    if from_city not in CITIES or to_city not in CITIES:
        raise HTTPException(status_code=400, detail="Unknown city. Please go to /cities endpoint a list of cities.")
    
    ctm_results, supra_results = await asyncio.gather(
        search_ctm(from_city, to_city, travel_date),
        search_supratours(from_city, to_city, travel_date),
    )
 
    results = ctm_results + supra_results # gather results together
    results.sort(key=lambda d: d.departure)
    return results

# TODO: add urban providers? and split scheduled and live hours