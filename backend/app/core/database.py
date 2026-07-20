# Database configuration and connection management
import firebase_admin
from firebase_admin import credentials, firestore
import os

def get_db():
    """
    Inicializa y retorna la instancia de Firestore.
    Implementa un patrón Singleton para evitar múltiples inicializaciones.
    """
    if not firebase_admin._apps:
        # Busca el archivo credentials.json en la carpeta 'backend'
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cred_path = os.path.join(base_dir, "credentials.json")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path}.")
            
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    return db
