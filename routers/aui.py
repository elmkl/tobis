import json
import pathlib
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/urban/ifrane-aui", tags=["Urban"])
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

@router.get("/schedule")
async def aui_schedule():
    path = DATA_DIR / "aui_shuttle.json"
    if not path.exists():
        raise HTTPException(404, "aui_shuttle.json not found in data/")
    return json.loads(path.read_text())