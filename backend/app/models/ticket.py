# Ticket model definition
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone

class TipoTicket(str, Enum):
    incidente = "Incidente"
    requerimiento = "Requerimiento"

class PriorityEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"

class UrgencyEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"

class LevelEnum(str, Enum):
    tier_1 = "Tier 1"
    tier_2 = "Tier 2"
    tier_3 = "Tier 3"

class TicketCreate(BaseModel):
    type: TipoTicket = Field(..., description="Clasificación obligatoria: Incidente o Requerimiento")
    account: str = Field(..., description="Cuenta o departamento del solicitante", example="Sample Account")
    site: str = Field(..., description="Ubicación física o sitio", example="Sample Site")
    category: str = Field(..., description="Categoría principal", example="Printer")
    subcategory: str = Field(..., description="Subcategoría asociada", example="Tray1")
    item: str = Field(..., description="Elemento específico afectado", example="Paper Jam")
    level: LevelEnum = Field(default=LevelEnum.tier_1, description="Nivel de soporte asignado")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Prioridad del ticket")
    urgency: UrgencyEnum = Field(default=UrgencyEnum.medium, description="Urgencia del ticket")
    subject: str = Field(..., description="Asunto breve del ticket")
    description: Optional[str] = Field(None, description="Descripción detallada del problema o solicitud")

class TicketDB(TicketCreate):
    id: str
    status: str = "Open"
    created_at: datetime
