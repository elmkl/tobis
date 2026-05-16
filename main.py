import asyncio
import pytz
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from data.cities import CITIES
from models.journey import Journey
from routers import alsa, casabus, ctm, sapst, supratours, aui, laayoune, markoub, oncf, amalway, casatramway
from routers.ctm import search_ctm
from routers.supratours import search_supratours
from routers.markoub import search_markoub
from routers.oncf import search_oncf
# scaffolding
app = FastAPI(title="tobis", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# high iq play
router_modules = [
    ctm.router, 
    supratours.router, 
    casabus.router, 
    alsa.router, 
    sapst.router, 
    aui.router, 
    laayoune.router, 
    markoub.router,
    oncf.router,
    amalway.router,
    casatramway.router
]

for module in router_modules:
    app.include_router(module)

morocco_timezone = pytz.timezone("Africa/Casablanca")

def get_current_time():
    return datetime.now(morocco_timezone)

def update_journey_status(journey: Journey) -> Journey:
    current_time = get_current_time()
    
    departure_time = datetime.fromisoformat(journey.departure)
    arrival_time = datetime.fromisoformat(journey.arrival)
    
    if departure_time.tzinfo is None:
        departure_time = morocco_timezone.localize(departure_time)
    if arrival_time.tzinfo is None:
        arrival_time = morocco_timezone.localize(arrival_time)
        
    if current_time < departure_time:
        journey.status = "scheduled"
    elif departure_time <= current_time <= arrival_time:
        journey.status = "running"
    else:
        journey.status = "arrived"
        
    return journey

@app.get("/")
async def root():
    return {"name": "tobis", "version": "0.1.0", "status": "ok", "human": "pls go on /portal"}

@app.get("/logo.png", include_in_schema=False)
async def serve_logo():
    return FileResponse("logo.png")

@app.get("/portal", response_class=FileResponse)
async def web_portal():
    return "portal.html"

@app.get("/time")
async def current_time_endpoint():
    current_time = get_current_time()
    return {
        "time": current_time.strftime("%H:%M"), 
        "datetime": current_time.isoformat(), 
        "timezone": "Africa/Casablanca"
    }

@app.get("/cities")
async def list_cities():
    return {"count": len(CITIES), "cities": sorted(CITIES.keys())}

@app.get("/national/search", response_model=list[Journey])
async def search_national_routes(
    from_city: str = Query(..., alias="from"), 
    to_city: str = Query(..., alias="to"), 
    travel_date: date = Query(default_factory=date.today)
):
    origin_city = from_city.lower().strip()
    destination_city = to_city.lower().strip()

    if origin_city not in CITIES or destination_city not in CITIES:
        raise HTTPException(status_code=400, detail="Unknown city.")

    # all apis
    ctm_res, supra_res, markoub_res, oncf_res = await asyncio.gather(
        search_ctm(origin_city, destination_city, travel_date),
        search_supratours(origin_city, destination_city, travel_date),
        search_markoub(origin_city, destination_city, travel_date),
        search_oncf(origin_city, destination_city, travel_date)
    )

    all_journeys = ctm_res + supra_res + markoub_res + oncf_res
    
    unique_journeys = {}
    for journey in all_journeys:
        # signature for trips
        trip_signature = (journey.departure, journey.destination, journey.price)
        
        if trip_signature not in unique_journeys:
            updated_journey = update_journey_status(journey)
            unique_journeys[trip_signature] = updated_journey
            
    processed_results = list(unique_journeys.values())
    processed_results.sort(key=lambda item: item.departure)
    
    return processed_results