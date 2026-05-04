from datetime import date

import httpx
from fastapi import APIRouter, HTTPException

from data.cities import CITIES
from models.journey import Journey

router = APIRouter(prefix="/operators/supratours", tags=["Supratours / ONCF"])
http = httpx.AsyncClient(
    timeout=15,
    verify=False,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Origin": "https://www.supratours.ma",
        "Referer": "https://www.supratours.ma/",
    },
)

async def search_supratours(origin: str, destination: str, travel_date: date) -> list[Journey]:
    o = CITIES.get(origin)
    d = CITIES.get(destination)
    if not o or not d or not o.get("supratours_code") or not d.get("supratours_code"):
        return []

    payload = {
        "codeGareDepart": o["supratours_code"],
        "codeGareArrivee": d["supratours_code"],
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
        trajets = r.json()["body"].get("listTrajetsAller", [])
    except Exception as e:
        print(f"[Supratours] search failed: {e}")
        return []

    results = []
    for t in trajets:
        seg = t["listeSegments"][0]
        voyageur = t["listeVoyageurs"][0] if t.get("listeVoyageurs") else {}
        prix_segments = voyageur.get("prixSegments", [])
        price = prix_segments[0]["prix"] if prix_segments else None
        is_bus = seg.get("codeClassification", "").lower() == "au"

        results.append(Journey(
            operator="Supratours" if is_bus else "ONCF",
            origin=seg["GareDepart"]["descriptionFr"],
            destination=seg["GareArrivee"]["descriptionFr"],
            departure=t["dateTimeDepart"],
            arrival=t["dateTimeArrivee"],
            duration=t["durationTrajet"],
            price=price,
            available_seats=None,
            brand=seg.get("codeClassification"),
        ))
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