import httpx
from fastapi import APIRouter, HTTPException

from app.kie_client import get_kie_client

router = APIRouter(prefix="/credit", tags=["credit"])


@router.get("")
async def get_credit():
    kie = get_kie_client()
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            return await kie.get_credit_balance(client)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"kie.ai недоступен: {exc}") from exc
