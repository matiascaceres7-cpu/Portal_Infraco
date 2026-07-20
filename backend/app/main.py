# Main entry point for FastAPI application
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tickets, users

app = FastAPI(
    title="IT Service Desk API",
    description="Backend robusto para portal de servicios de TI, diseñado bajo estándares ITIL.",
    version="1.0.0"
)

# Configuración CORS para despliegue en nube
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(users.router)

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Service Desk API operativa"}
