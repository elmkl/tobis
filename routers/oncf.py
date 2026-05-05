import httpx
from datetime import date
from fastapi import APIRouter
from data.cities import CITIES
from models.journey import Journey

router = APIRouter(prefix="/national/oncf", tags=["National"])
http_client = httpx.AsyncClient(timeout=20, verify=False)

async def search_oncf(origin: str, destination: str, travel_date: date):
    origin_data = CITIES.get(origin)
    dest_data = CITIES.get(destination)

    if not origin_data or not dest_data:
        return []

    origin_code = origin_data.get("oncf_code")
    dest_code = dest_data.get("oncf_code")

    if not origin_code or not dest_code:
        return []

    payload = {
        "codeGareDepart": origin_code,
        "codeGareArrivee": dest_code,
        "codeNiveauConfort": 2,
        "dateDepartAller": f"{travel_date.isoformat()}T00:01:00+01:00",
        "dateDepartAllerMax": None,
        "dateDepartRetour": None,
        "dateDepartRetourMax": None,
        "isTrainDirect": None,
        "isPreviousTrainAller": None,
        "isTarifReduit": True,
        "adulte": 1,
        "kids": 0,
        "listVoyageur": [{"numeroClient": None, "codeTarif": None, "codeProfilDemographique": "3", "dateNaissance": None}],
        "booking": False,
        "isEntreprise": False,
        "token": "",
        "numeroContract": "",
        "codeTiers": "",
        "iTravel": False,
        "isActive": False
    }

    try:
        response = await http_client.post("https://www.oncf-voyages.ma/api/schedule", json=payload)
        response.raise_for_status()
        data = response.json()
        
        body = data.get("body", {})
        if not body:
            return []
            
        journeys_data = body.get("departurePath", [])
    except Exception as e:
        print(f"[ONCF] Search failed for {origin} to {destination}: {e}")
        return []

    results = []
    for journey in journeys_data:
        segments = journey.get("listSegments", [])
        if not segments:
            continue
        first_segment = segments[0]
        
        # flexible and non flexible pricing
        price = None
        flexibility_list = journey.get("listPrixFlexibilite", [])
        if flexibility_list:
            prices_array = flexibility_list[0].get("prixFlexibilite", [])
            if prices_array:
                price = prices_array[0].get("prix")
                
        # Figure out train from class code
        classification = first_segment.get("codeClassification", "").upper()
        if classification == "RGV":
            operator_name = "ONCF (Al Boraq)"
            brand_name = "High Speed Train"
        elif classification == "TL":
            operator_name = "ONCF (Al Atlas)"
            brand_name = "Intercity Train"
        elif classification == "TNR":
            operator_name = "ONCF (TNR)"
            brand_name = "Rapid Train"
        elif classification == "AU":
            operator_name = "Supratours (via ONCF)"
            brand_name = "Bus Relay"
        else:
            operator_name = f"ONCF ({classification})"
            brand_name = classification
        
        # station numbers to names
        results.append(Journey(
            operator=operator_name,
            origin=origin.title(),
            destination=destination.title(),
            departure=journey.get("dateTimeDepart"),
            arrival=journey.get("dateTimeArrivee"),
            duration=journey.get("durationTrajet", "Unknown"),
            price=price,
            available_seats=None,
            amenities=[],
            brand=brand_name
        ))
        
    return results