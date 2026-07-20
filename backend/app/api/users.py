# Users API endpoints
from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, UserDB
from app.core.database import get_db
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


@router.post("/", response_model=UserDB, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    """
    Crea un nuevo usuario en Firestore validando los datos de entrada.
    """
    try:
        db = get_db()
        users_ref = db.collection("users")
        
        user_data = user_in.model_dump()
        user_data["created_at"] = datetime.now(timezone.utc)
        user_data["is_active"] = True
        
        update_time, doc_ref = users_ref.add(user_data)
        
        return UserDB(id=doc_ref.id, **user_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la creación del usuario: {str(e)}"
        )


@router.get("/", response_model=list[UserDB], status_code=status.HTTP_200_OK)
async def list_users():
    """
    Recupera la lista de todos los usuarios registrados desde Firestore.
    """
    try:
        db = get_db()
        users_ref = db.collection("users")
        
        # Recuperar todos los documentos de la colección
        docs = users_ref.stream()
        
        users_list = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            users_list.append(user_data)
            
        return users_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recuperar el listado de usuarios: {str(e)}"
        )
