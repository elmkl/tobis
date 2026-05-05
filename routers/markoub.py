import httpx
import urllib.parse
import json
from datetime import date
from fastapi import APIRouter
from data.cities import CITIES
from models.journey import Journey

# national aggregator
router = APIRouter(prefix="/national/markoub", tags=["National"])
http_client = httpx.AsyncClient(timeout=20)

async def search_markoub(origin: str, destination: str, travel_date: date) -> list[Journey]:
    origin_data = CITIES.get(origin)
    dest_data = CITIES.get(destination)
    
    if not origin_data or not dest_data:
        return []
        
    origin_id = origin_data.get("markoub_id")
    dest_id = dest_data.get("markoub_id")
    
    if not origin_id or not dest_id:
        return []

    input_payload = {
        "0": {
            "json": {
                "arrivalCityId": dest_id,
                "departureCityId": origin_id,
                "date": travel_date.isoformat(),
                "nbrOfPassengers": 1,
                "searchType": "direct",
                "searchId": None,
                "reconversionId": None
            }
        }
    }
    
    encoded_input = urllib.parse.quote(json.dumps(input_payload))
    url = f"https://markoub.ma/api/trpc/bookingFlow.getJourneys?batch=1&input={encoded_input}"
    
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
        journeys_data = data[0]["result"]["data"]["json"]["journeys"]
    except Exception as e:
        print(f"[Markoub] Search failed for {origin} to {destination}: {e}")
        return []

    results = []
    for journey in journeys_data:
        # skip CTM and supratours 
        if journey.get("inventory") == "ctm" and journey.get("inventory") == "supratours":
            continue
            
        company_info = journey.get("company", {})
        company_name = company_info.get("name", "Unknown Operator")
        
        from_data = journey.get("from", {})
        to_data = journey.get("to", {})
        
        dep_date = from_data.get("date", travel_date.isoformat())
        dep_time = from_data.get("time", "00:00:00")
        departure_iso = f"{dep_date}T{dep_time}"
        
        arr_date = to_data.get("date", travel_date.isoformat())
        arr_time = to_data.get("time", "00:00:00")
        arrival_iso = f"{arr_date}T{arr_time}"
        
        price_data = journey.get("price", {})
        total_price = price_data.get("totalFinalPrice")
        
        amenities_list = []
        equipments = journey.get("equipments")
        if equipments:
            for item in equipments:
                amenities_list.append(item.get("name"))
        
        results.append(Journey(
            operator=f"Markoub ({company_name})",
            origin=from_data.get("stationName", origin.capitalize()),
            destination=to_data.get("stationName", destination.capitalize()),
            departure=departure_iso,
            arrival=arrival_iso,
            duration=journey.get("duration", "Unknown"),
            price=total_price,
            available_seats=journey.get("seatsLeft"),
            amenities=amenities_list,
            for_sale=not journey.get("isSoldOut", False)
        ))
        
    return results