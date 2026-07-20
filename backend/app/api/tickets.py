# Tickets API endpoints
from fastapi import APIRouter, HTTPException, status
from app.models.ticket import TicketCreate, TicketDB
from app.core.database import get_db
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["Tickets"]
)

@router.post("/", response_model=TicketDB, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_in: TicketCreate):
    """
    Crea un nuevo ticket en Firestore validando los datos de entrada.
    """
    try:
        db = get_db()
        tickets_ref = db.collection("tickets")
        
        ticket_data = ticket_in.model_dump()
        ticket_data["created_at"] = datetime.now(timezone.utc)
        ticket_data["status"] = "Open"
        
        update_time, doc_ref = tickets_ref.add(ticket_data)
        
        return TicketDB(id=doc_ref.id, **ticket_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la creación del ticket: {str(e)}"
        )
