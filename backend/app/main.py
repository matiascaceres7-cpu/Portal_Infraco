# Main entry point for FastAPI application
from fastapi import FastAPI
from app.api import tickets

app = FastAPI(
    title="IT Service Desk API",
    description="Backend robusto para portal de servicios de TI, diseñado bajo estándares ITIL.",
    version="1.0.0"
)

app.include_router(tickets.router)

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Service Desk API operativa"}
