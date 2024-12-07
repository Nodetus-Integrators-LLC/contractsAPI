from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import quote
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import feedparser
import xml.etree.ElementTree as ET

class SearchCriteria(BaseModel):
    last_mod_date: Optional[Tuple[datetime, datetime]] = None
    agency_code: Optional[str] = None
    agency_name: Optional[str] = None
    award_status: Optional[str] = None
    contract_type: Optional[str] = None
    piid: Optional[str] = None
    vendor_uei: Optional[str] = None
    cage_code: Optional[str] = None
    naics_code: Optional[str] = None
    
    def build_url(self, base_url: str) -> str:
        criteria = []
        
        if self.last_mod_date:
            start, end = self.last_mod_date
            criteria.append(f'LAST_MOD_DATE:[{start:%Y/%m/%d},{end:%Y/%m/%d}]')
            
        if self.agency_code:
            criteria.append(f'AGENCY_CODE:"{self.agency_code}"')
            
        if self.agency_name:
            criteria.append(f'AGENCY_NAME:"{quote(self.agency_name)}"')
            
        if self.award_status:
            criteria.append(f'AWARD_STATUS:"{self.award_status}"')
            
        if self.contract_type:
            criteria.append(f'CONTRACT_TYPE:"{self.contract_type}"')
            
        if self.piid:
            criteria.append(f'PIID:"{self.piid}"')
            
        if self.vendor_uei:
            criteria.append(f'VENDOR_UEI:"{self.vendor_uei}"')
            
        if self.cage_code:
            criteria.append(f'CAGE_CODE:"{self.cage_code}"')
            
        if self.naics_code:
            criteria.append(f'PRINCIPAL_NAICS_CODE:"{self.naics_code}"')
            
        return base_url + ''.join(criteria)

class ContractAward(BaseModel):
    piid: str
    agency_code: str
    agency_name: str
    award_status: str
    date_signed: datetime
    obligated_amount: float
    vendor_uei: str
    cage_code: Optional[str] = None
    naics_code: Optional[str] = None

class Neo4jAtomProcessor:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def process_feed(self, search_criteria: SearchCriteria, base_url: str) -> List[ContractAward]:
        feed_url = search_criteria.build_url(base_url)
        feed = feedparser.parse(feed_url)
        awards = []
        
        for entry in feed.entries:
            award_content = entry.content[0].value if entry.content else ""
            award = self._parse_award_xml(award_content)
            if award:
                awards.append(award)
                self._store_award(award)
        
        return awards

    def _parse_award_xml(self, xml_content: str) -> Optional[ContractAward]:
        try:
            root = ET.fromstring(xml_content)
            ns = {'ns': 'https://www.fpds.gov/FPDS'}
            
            # Extract basic award info
            award_data = {
                'piid': root.find('.//ns:PIID', ns).text,
                'agency_code': root.find('.//ns:agencyID', ns).text,
                'agency_name': root.find('.//ns:agencyID', ns).attrib.get('name', ''),
                'award_status': root.find('.//ns:status', ns).attrib.get('description', ''),
                'date_signed': datetime.fromisoformat(root.find('.//ns:signedDate', ns).text.split()[0]),
                'obligated_amount': float(root.find('.//ns:obligatedAmount', ns).text),
                'vendor_uei': root.find('.//ns:UEI', ns).text if root.find('.//ns:UEI', ns) is not None else '',
                'cage_code': root.find('.//ns:cageCode', ns).text if root.find('.//ns:cageCode', ns) is not None else None,
                'naics_code': root.find('.//ns:principalNAICSCode', ns).text if root.find('.//ns:principalNAICSCode', ns) is not None else None
            }
            
            return ContractAward(**award_data)
        except Exception as e:
            print(f"Error parsing award XML: {e}")
            return None

    def _store_award(self, award: ContractAward):
        with self.driver.session() as session:
            session.execute_write(self._create_award_node, award)

    @staticmethod
    def _create_award_node(tx, award: ContractAward):
        query = """
        MERGE (a:Award {piid: $piid})
        SET a.agency_code = $agency_code,
            a.agency_name = $agency_name,
            a.award_status = $award_status,
            a.date_signed = datetime($date_signed),
            a.obligated_amount = $obligated_amount
        
        MERGE (v:Vendor {uei: $vendor_uei})
        SET v.cage_code = $cage_code
        
        WITH a, v
        WHERE $naics_code IS NOT NULL
        MERGE (n:NAICS {code: $naics_code})
        MERGE (a)-[:CATEGORIZED_AS]->(n)
        
        MERGE (a)-[:AWARDED_TO]->(v)
        """
        
        # Convert datetime to string format Neo4j expects
        award_dict = award.dict()
        award_dict['date_signed'] = award_dict['date_signed'].isoformat()
        
        tx.run(query, award_dict)

    def get_vendor_awards(self, vendor_uei: str) -> List[ContractAward]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (v:Vendor {uei: $uei})<-[:AWARDED_TO]-(a:Award)
                RETURN a
                ORDER BY a.date_signed DESC
            """, {"uei": vendor_uei})
            return [ContractAward(**record["a"]) for record in result]