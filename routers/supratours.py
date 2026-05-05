from datetime import date
import asyncio

import httpx
from fastapi import APIRouter, HTTPException

from data.cities import CITIES
from models.journey import Journey

router = APIRouter(prefix="/national/supratours", tags=["National"])
http = httpx.AsyncClient(
    timeout=15,
    verify=False,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Origin": "https://www.supratours.ma",
        "Referer": "https://www.supratours.ma/",
    },
)

async def _query(origin_code: str, dest_code: str, travel_date: date) -> list[Journey]:
    payload = {
        "codeGareDepart": origin_code,
        "codeGareArrivee": dest_code,
        "codeNiveauConfort": "2",
        "dateDepartAller": f"{travel_date.isoformat()}T06:00:00+01:00",
        "dateDepartAllerMax": None,
        "dateDepartRetour": None,
        "dateDepartRetourMax": None,
        "isTrainDirect": None,
        "isPreviousTrainAller": None,
        "listVoyageur": [
            {"numeroClient": None, "codeTarif": None, "codeProfilDemographique": "3", "dateNaissance": None}
        ],
    }
    try:
        r = await http.post("https://www.supratours.ma/api/disponibilite", json=payload)
        r.raise_for_status()
        body = r.json().get("body")
        if not body:
            return []
        trajets = body.get("listTrajetsAller", [])
    except Exception as e:
        print(f"[Supratours] {origin_code}→{dest_code} failed: {e}")
        return []

    results = []
    for t in trajets:
        seg = t["listeSegments"][0] if t.get("listeSegments") else None
        if not seg:
            continue
        depart = seg.get("GareDepart")
        arrivee = seg.get("GareArrivee")
        if not depart or not arrivee:
            continue
        voyageur = t["listeVoyageurs"][0] if t.get("listeVoyageurs") else {}
        prix_segments = voyageur.get("prixSegments", [])
        price = prix_segments[0]["prix"] if prix_segments else None
        is_bus = seg.get("codeClassification", "").lower() == "au"
        results.append(Journey(
            operator="Supratours" if is_bus else "ONCF",
            origin=depart["descriptionFr"],
            destination=arrivee["descriptionFr"],
            departure=t["dateTimeDepart"],
            arrival=t["dateTimeArrivee"],
            duration=t["durationTrajet"],
            price=price,
            available_seats=None,
            brand=seg.get("codeClassification"),
        ))
    return results

async def search_supratours(origin: str, destination: str, travel_date: date) -> list[Journey]:
    o = CITIES.get(origin)
    d = CITIES.get(destination)
    if not o or not d:
        return []

    # support multiple codes per city (e.g. casablanca has 3 stops)
    origin_codes = o.get("supratours_codes") or ([o["supratours_code"]] if o.get("supratours_code") else [])
    dest_codes = d.get("supratours_codes") or ([d["supratours_code"]] if d.get("supratours_code") else [])
    if not origin_codes or not dest_codes:
        return []

    # query all stations in parallel
    tasks = [_query(oc, dc, travel_date) for oc in origin_codes for dc in dest_codes]
    all_results = await asyncio.gather(*tasks)

    # flatten and deduplicate by departure time + destination
    seen = set()
    results = []
    for batch in all_results:
        for j in batch:
            key = (j.departure, j.destination)
            if key not in seen:
                seen.add(key)
                results.append(j)
    return results

@router.get("/stops")
async def supratours_stops():
    # NOTE: these have GPS co-ordinates
    try:
        r = await http.get("https://www.supratours.ma/api/stations")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))