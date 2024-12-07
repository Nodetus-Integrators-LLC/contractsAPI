# Location: tests/test_feed_processor.py

import pytest
from datetime import datetime
from neo4j import GraphDatabase
from app.services.processor import Neo4jAtomProcessor, SearchCriteria, ContractAward

@pytest.fixture
def processor():
    proc = Neo4jAtomProcessor(
        "bolt://localhost:7687",
        "neo4j",
        "test_password"
    )
    yield proc
    proc.close()

@pytest.fixture
def sample_criteria():
    return SearchCriteria(
        agency_code="1234",
        award_status="Final",
        last_mod_date=(
            datetime(2023, 1, 1),
            datetime(2023, 12, 31)
        )
    )

def test_url_construction(sample_criteria):
    base_url = "https://api.example.gov/atom/"
    url = sample_criteria.build_url(base_url)
    assert "AGENCY_CODE:\"1234\"" in url
    assert "AWARD_STATUS:\"Final\"" in url
    assert "LAST_MOD_DATE:[2023/01/01,2023/12/31]" in url

@pytest.mark.asyncio
async def test_process_feed(processor, sample_criteria, mocker):
    mock_feed = mocker.patch('feedparser.parse')
    mock_feed.return_value.entries = [{
        'id': 'TEST123',
        'agency_code': '1234',
        'agency_name': 'Test Agency',
        'award_status': 'Final',
        'published_parsed': datetime.now().timestamp(),
        'obligated_amount': '1000.00'
    }]
    
    awards = processor.process_feed(sample_criteria, "http://test.com")
    assert len(awards) == 1
    assert awards[0].piid == 'TEST123'

# Location: tests/test_api.py

from fastapi.testclient import TestClient
from app.api.v1.feed_routes import router
from app.core.config import Settings

client = TestClient(router)

def test_process_feed_endpoint():
    response = client.post("/api/v1/process-feed", json={
        "agency_code": "1234",
        "award_status": "Final"
    })
    assert response.status_code == 200
    assert "processed_count" in response.json()

def test_get_awards_endpoint():
    response = client.get("/api/v1/awards", params={
        "agency_code": "1234",
        "start_date": "2023-01-01T00:00:00"
    })
    assert response.status_code == 200
    assert isinstance(response.json(), list)