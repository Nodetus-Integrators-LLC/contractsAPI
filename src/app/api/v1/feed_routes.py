from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from core.config import Settings
from services.processor import SearchCriteria, ContractAward, Neo4jAtomProcessor

router = APIRouter(prefix="/api/v1")

class ProcessFeedResponse(BaseModel):
    processed_count: int
    awards: List[ContractAward]

async def get_processor():
    settings = Settings()
    processor = Neo4jAtomProcessor(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password
    )
    try:
        yield processor
    finally:
        processor.close()

@router.post("/process-feed", response_model=ProcessFeedResponse)
async def process_feed(
    criteria: SearchCriteria,
    processor: Neo4jAtomProcessor = Depends(get_processor)
):
    try:
        awards = processor.process_feed(criteria, Settings().base_atom_url)
        return ProcessFeedResponse(
            processed_count=len(awards),
            awards=awards
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/awards", response_model=List[ContractAward])
async def get_awards(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agency_code: Optional[str] = None,
    vendor_uei: Optional[str] = None,
    processor: Neo4jAtomProcessor = Depends(get_processor)
):
    query = """
    MATCH (a:Award)
    WHERE 
        ($start_date IS NULL OR a.date_signed >= datetime($start_date))
        AND ($end_date IS NULL OR a.date_signed <= datetime($end_date))
        AND ($agency_code IS NULL OR a.agency_code = $agency_code)
        AND ($vendor_uei IS NULL OR (a)-[:AWARDED_TO]->(:Vendor {uei: $vendor_uei}))
    RETURN a
    ORDER BY a.date_signed DESC
    LIMIT 100
    """
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "agency_code": agency_code,
        "vendor_uei": vendor_uei
    }
    
    with processor.driver.session() as session:
        results = session.run(query, params)
        return [ContractAward(**record["a"]) for record in results]

@router.get("/vendor/{uei}", response_model=dict)
async def get_vendor_summary(
    uei: str,
    processor: Neo4jAtomProcessor = Depends(get_processor)
):
    query = """
    MATCH (v:Vendor {uei: $uei})<-[:AWARDED_TO]-(a:Award)
    WITH v, 
         count(a) as award_count,
         sum(a.obligated_amount) as total_obligated,
         collect(DISTINCT a.agency_code) as agencies
    RETURN {
        uei: v.uei,
        cage_code: v.cage_code,
        award_count: award_count,
        total_obligated: total_obligated,
        agency_count: size(agencies),
        agencies: agencies
    } as summary
    """
    
    with processor.driver.session() as session:
        result = session.run(query, {"uei": uei}).single()
        if not result:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return result["summary"]