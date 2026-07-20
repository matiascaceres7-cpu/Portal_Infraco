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

@router.get("/", response_model=list[TicketDB], status_code=status.HTTP_200_OK)
async def list_tickets():
    """
    Recupera el historial completo de tickets desde Firestore.
    Ideal para auditoría, exportación de datos y respaldos.
    """
    try:
        db = get_db()
        tickets_ref = db.collection("tickets")
        
        # Recuperar todos los documentos de la colección
        docs = tickets_ref.stream()
        
        tickets_list = []
        for doc in docs:
            ticket_data = doc.to_dict()
            ticket_data["id"] = doc.id
            tickets_list.append(ticket_data)
            
        return tickets_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recuperar el historial de tickets: {str(e)}"
        )
