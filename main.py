import asyncio
from datetime import date
from typing import Optional
 
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
 
# scaffolding
app = FastAPI(title="tobis", description="API for public transit in Morocco", version="0.1.0",)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],)
 
# TODO: add routers
 
@app.get("/")
async def root():
    return {"name": "tobis", "version": "0.1.0", "status": "ok"}
