import httpx
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException
from data.cities import CITIES
from models.journey import Journey

router = APIRouter(prefix="/operators/ctm", tags=["CTM"])
http = httpx.AsyncClient(timeout=15)

async def search_ctm(origin: str, destination: str, travel_date: date) -> list[Journey]:
    o = CITIES.get(origin)
    d = CITIES.get(destination)
    if not o or not d or not o.get("ctm_stop_id") or not d.get("ctm_city_id"):
        return []

    params = {
        "departureDate": travel_date.isoformat(),
        "isPartOfRoundtrip": "false",
        "currency": "CURRENCY.MAD",
        "fareClasses": "BONUS_SCHEME_GROUP.ADULT,1",
        "originBusStopId": o["ctm_stop_id"],
        "destinationCityId": d["ctm_city_id"],
        "IsOutbound": "true",
        "CheckPaxSoldTogetherRules": "true",
    }

    try:
        r = await http.get("https://booking.ctm.ma/api/fr-fr/journeys/search", params=params)
        r.raise_for_status()
        journeys = r.json().get("Journeys", [])
    except Exception:
        return []

    results = []
    for j in journeys:
        leg = j["Legs"][0]
        results.append(Journey(
            operator="CTM",
            origin=j["OriginStopName"],
            destination=j["DestinationStopName"],
            departure=j["DepartureDateTime"],
            arrival=j["ArrivalDateTime"],
            duration=j["Duration"],
            price=j.get("RegularPrice"),
            available_seats=j.get("AvailableRegularSeats"),
            amenities=[e["EquipmentName"] for e in leg.get("AvailableEquipment", [])],
            brand=leg.get("BrandName"),
            for_sale=j.get("IsForSale", False),
        ))
    return results

@router.get("/stops")
async def ctm_stops():
    # NOTE: these have GPS co-ordinates
    try:
        r = await http.get("https://booking.ctm.ma/api/fr-fr/filtered-stops?onlyWithValidTrips=true")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))