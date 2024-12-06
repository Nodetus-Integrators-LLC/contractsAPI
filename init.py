from pathlib import Path
import shutil
import os
from typing import Dict, Optional
import json

class MicroserviceTemplateGenerator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
    def generate(self, service_name: str, config: Dict) -> None:
        """Generate microservice structure from template"""
        service_path = self.base_path / service_name
        
        # Create base directories
        directories = [
            'app',
            'app/api',
            'app/core',
            'app/models',
            'app/schemas',
            'app/services',
            'app/utils',
            'tests',
            'tests/api',
            'tests/services'
        ]
        
        for dir_path in directories:
            (service_path / dir_path).mkdir(parents=True, exist_ok=True)
            
        # Generate core files
        self._generate_main(service_path, service_name, config)
        self._generate_docker_files(service_path, service_name, config)
        self._generate_api_files(service_path)
        self._generate_service_files(service_path)
        self._generate_test_files(service_path)
        self._generate_config_files(service_path, config)

    def _generate_main(self, path: Path, service_name: str, config: Dict) -> None:
        main_content = f"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router

app = FastAPI(
    title="{service_name}",
    description="{config.get('description', '')}",
    version="{config.get('version', '0.1.0')}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}
"""
        (path / 'app' / 'main.py').write_text(main_content)

    def _generate_docker_files(self, path: Path, service_name: str, config: Dict) -> None:
        dockerfile = f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        (path / 'Dockerfile').write_text(dockerfile)

        compose = f"""version: '3.8'
services:
  {service_name}:
    build: .
    ports:
      - "{config.get('port', 8000)}:8000"
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
    volumes:
      - .:/app
    networks:
      - microservices-network

networks:
  microservices-network:
    external: true
"""
        (path / 'docker-compose.yml').write_text(compose)

    def _generate_api_files(self, path: Path) -> None:
        routes = """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "API is running"}
"""
        (path / 'app' / 'api' / 'routes.py').write_text(routes)

    def _generate_service_files(self, path: Path) -> None:
        service = """from typing import Optional, List, Dict, Any

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
"""
        (path / 'app' / 'services' / 'base.py').write_text(service)

    def _generate_test_files(self, path: Path) -> None:
        test_content = """import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
"""
        (path / 'tests' / 'test_main.py').write_text(test_content)

    def _generate_config_files(self, path: Path, config: Dict) -> None:
        settings = """from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str
    CORS_ORIGINS: List[str] = ["*"]
    DATABASE_URL: str
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
"""
        (path / 'app' / 'core' / 'config.py').write_text(settings)

        requirements = """fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.5.2
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
httpx>=0.25.2
pytest>=7.4.3
pytest-asyncio>=0.21.1
"""
        (path / 'requirements.txt').write_text(requirements)

def create_microservice(name: str, config: Dict) -> None:
    generator = MicroserviceTemplateGenerator("./services")
    generator.generate(name, config)

# Example usage:
if __name__ == "__main__":
    config = {
        "description": "Example Microservice API",
        "version": "0.1.0",
        "port": 8000
    }
    create_microservice("example-service", config)