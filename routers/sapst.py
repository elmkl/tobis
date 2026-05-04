import json
import pathlib
from fastapi import APIRouter, HTTPException
 
router = APIRouter(prefix="/urban/taghazout-bay", tags=["Urban"])
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# TODO: maybe one file for all static data? and map the stations on jsons to geo coordinates
@router.get("/schedule")
async def sapst_schedule():
    path = DATA_DIR / "sapst_taghazout_bay.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="sapst_taghazout_bay.json not found in data/")
    return json.loads(path.read_text())