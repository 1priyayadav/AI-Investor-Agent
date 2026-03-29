from fastapi import APIRouter, Depends

from backend.api.deps import TokenData, get_current_user, get_optional_user
from backend.services.nse_universe_scanner import nse_universe_scanner
from backend.services.opportunity_radar import opportunity_radar

router = APIRouter()


@router.post("/refresh")
async def refresh_radar(current_user: TokenData = Depends(get_current_user)):
    sigs = opportunity_radar.refresh_global_signals()
    return {"status": "ok", "count": len(sigs)}


@router.get("/opportunities")
async def list_opportunities(current_user: TokenData = Depends(get_optional_user)):
    return {"signals": opportunity_radar.get_signals(80)}


@router.get("/nse-patterns")
async def nse_patterns(current_user: TokenData = Depends(get_optional_user)):
    return {"patterns": nse_universe_scanner.latest_patterns(50)}


@router.post("/nse-scan")
async def run_nse_scan(current_user: TokenData = Depends(get_current_user)):
    rows = nse_universe_scanner.scan_batch()
    return {"status": "ok", "pattern_rows": len(rows)}
