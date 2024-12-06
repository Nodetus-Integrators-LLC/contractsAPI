# app/api/v1/endpoints/vendors.py
from fastapi import APIRouter, Depends
from app.schemas.vendor import VendorAnalysis
from app.services.market_research import VendorIntelligenceService

router = APIRouter()

@router.get("/vendors/{vendor_id}/analysis")
async def analyze_vendor(
    vendor_id: str,
    service: VendorIntelligenceService = Depends()
) -> VendorAnalysis:
    """
    Analyzes vendor performance, past contracts, and market position.
    Integrates with external data sources for comprehensive analysis.
    """
    return await service.analyze_vendor(vendor_id)