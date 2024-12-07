# src/app/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "API is working"}

@router.get("/health")
async def health():
    return {"status": "healthy"}