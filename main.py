import asyncio
from datetime import date
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from data.cities import CITIES
from routers import ctm, supratours, casabus

# scaffolding
app = FastAPI(title="tobis", description="API for public transit in Morocco", version="0.1.0",)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],)

# TODO: add more routers
app.include_router(ctm.router)
app.include_router(supratours.router)
app.include_router(casabus.router)

@app.get("/")
async def root():
    return {"name": "tobis", "version": "0.1.0", "status": "ok"}

@app.get("/cities")
async def list_cities():
    return {"count": len(CITIES), "cities": sorted(CITIES.keys())}