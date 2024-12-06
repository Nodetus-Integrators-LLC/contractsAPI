from typing import Optional, List, Dict, Any

class BaseService:
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
        
    async def list(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError
        
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
        
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
        
    async def delete(self, id: str) -> bool:
        raise NotImplementedError
