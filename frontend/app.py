import os
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

st.set_page_config(page_title="IT Service Desk", page_icon="🔧", layout="wide")
# --- CSS Personalizado para ocultar marca de Streamlit ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
st.title("Portal de Servicios TI")

# Construir ruta absoluta al logo basada en la ubicación de este script
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "Logo.png")

try:
    st.image(logo_path, width=250)
except Exception:
    st.warning("⚠️ No se encontró el archivo logo.png en el directorio del frontend.")

st.subheader("Sistema Integral de Gestión de Tickets y Usuarios")

# ============================================
# CONEXIÓN A FIRESTORE
# ============================================
@st.cache_resource
def get_firestore_client():
    """Inicializa y retorna el cliente de Firestore usando las credenciales de st.secrets"""
    try:
        # Obtener las credenciales desde st.secrets
        credentials_info = st.secrets["gcp_service_account"]
        
        # Crear las credenciales usando service_account
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Inicializar el cliente de Firestore
        db = firestore.Client(credentials=credentials, project=credentials.project_id)
        return db
    except KeyError:
        st.error("❌ No se encontraron las credenciales de GCP en st.secrets. Configure 'gcp_service_account'.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error al conectar con Firestore: {str(e)}")
        st.stop()

# Obtener la instancia del cliente
db = get_firestore_client()

# Mapeo de prioridad y urgencia (español -> inglés)
PRIORITY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}
URGENCY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}

# Crear las tres pestañas
tab1, tab2, tab3 = st.tabs(["Generar Ticket", "Historial de Tickets", "Gestión de Usuarios"])

# ============================================
# PESTAÑA 1: GENERAR TICKET
# ============================================
with tab1:
    st.header("📝 Generación de Tickets")
    st.write("Complete los parámetros del ticket (Estándar ManageEngine)")
    
    with st.form("ticket_form"):
        # Clasificación del Ticket con radio horizontal
        clasificacion = st.radio("Clasificación del Ticket", ["Incidente", "Requerimiento"], horizontal=True, key="clasificacion_ticket")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Empresa", value="Onnetfibra", key="empresa_ticket")
            ubicacion = st.selectbox("Ubicación", ["Piso 14", "Piso 15", "Remoto"], key="ubicacion_ticket")
            categoria = st.text_input("Categoría", value="Network", key="categoria_ticket")
            subcategoria = st.text_input("Subcategoría", value="WiFi", key="subcategoria_ticket")
        
        with col2:
            nivel = st.selectbox("Nivel", ["Tier 1", "Tier 2", "Tier 3"], index=0, key="nivel_ticket")
            prioridad_es = st.selectbox("Prioridad", ["Baja", "Media", "Alta"], key="prioridad_ticket")
            urgencia_es = st.selectbox("Urgencia", ["Baja", "Media", "Alta"], key="urgencia_ticket")
            elemento = st.text_input("Elemento Afectado", value="Cortes de señal y zonas de sombra", key="elemento_ticket")
        
        st.markdown("---")
        asunto = st.text_input("Asunto", value="Diagnóstico y optimización de red WiFi", key="asunto_ticket")
        descripcion = st.text_area("Descripción Detallada", placeholder="Ingrese los detalles del requerimiento o incidente...", key="descripcion_ticket")
        
        submitted = st.form_submit_button("✅ Crear Ticket")
        
        if submitted:
            # Mapeo de prioridad y urgencia a inglés
            prioridad = PRIORITY_MAP[prioridad_es]
            urgencia = URGENCY_MAP[urgencia_es]
            
            ticket_data = {
                "type": clasificacion,
                "account": empresa,
                "site": ubicacion,
                "category": categoria,
                "subcategory": subcategoria,
                "item": elemento,
                "level": nivel,
                "priority": prioridad,
                "urgency": urgencia,
                "subject": asunto,
                "description": descripcion
            }
            
            try:
                # Agregar el documento a la colección 'tickets' en Firestore
                doc_ref = db.collection('tickets').add(ticket_data)
                st.success(f"✅ Ticket creado exitosamente con ID: {doc_ref[1].id}")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al crear el ticket: {str(e)}")

# ============================================
# PESTAÑA 2: HISTORIAL DE TICKETS
# ============================================
with tab2:
    st.header("📊 Historial y Respaldo de Tickets")
    st.write("Visualización directa de la base de datos para auditoría y migración.")
    
    if st.button("🔄 Actualizar Historial", key="btn_historial"):
        try:
            # Leer todos los documentos de la colección 'tickets'
            tickets_list = []
            for doc in db.collection('tickets').stream():
                ticket_dict = doc.to_dict()
                ticket_dict['id'] = doc.id  # Incluir el ID del documento
                tickets_list.append(ticket_dict)
            
            if tickets_list:
                # --- Panel de Métricas ---
                total_tickets = len(tickets_list)
                total_incidentes = sum(1 for t in tickets_list if t.get("type") == "Incidente")
                total_req = sum(1 for t in tickets_list if t.get("type") == "Requerimiento")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Tickets", total_tickets)
                col2.metric("Incidentes", total_incidentes)
                col3.metric("Requerimientos", total_req)
                st.markdown("---")
                
                # Despliegue de la tabla
                st.dataframe(tickets_list, use_container_width=True)
            else:
                st.info("La base de datos está conectada, pero aún no hay tickets registrados.")
        except Exception as e:
            st.error(f"❌ Error al consultar Firestore: {str(e)}")

# ============================================
# PESTAÑA 3: GESTIÓN DE USUARIOS
# ============================================
with tab3:
    st.header("👥 Gestión de Usuarios")
    
    # Sección: Registrar nuevo usuario
    st.subheader("➕ Registrar Nuevo Usuario")
    
    with st.form("user_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("📧 Correo Electrónico", placeholder="usuario@example.com", key="email_user")
            full_name = st.text_input("👤 Nombre Completo", placeholder="Juan Pérez", key="full_name_user")
        
        with col2:
            department = st.text_input("🏢 Departamento", placeholder="Infraestructura TI", key="department_user")
            role = st.selectbox("🔐 Rol", ["user", "admin", "technician"], key="role_user")
        
        submitted_user = st.form_submit_button("✅ Registrar Usuario")
        
        if submitted_user:
            if not email or not full_name or not department:
                st.error("❌ Todos los campos son obligatorios.")
            else:
                user_data = {
                    "email": email,
                    "full_name": full_name,
                    "department": department,
                    "role": role
                }
                
                try:
                    # Agregar el usuario a la colección 'users' en Firestore
                    doc_ref = db.collection('users').add(user_data)
                    st.success(f"✅ Usuario registrado exitosamente con ID: {doc_ref[1].id}")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al registrar el usuario: {str(e)}")
    
    st.markdown("---")
    
    # Sección: Listar usuarios registrados
    st.subheader("📋 Usuarios Registrados")
    
    if st.button("🔄 Cargar Usuarios", key="btn_usuarios"):
        try:
            # Leer todos los documentos de la colección 'users'
            users_list = []
            for doc in db.collection('users').stream():
                user_dict = doc.to_dict()
                user_dict['id'] = doc.id  # Incluir el ID del documento
                users_list.append(user_dict)
            
            if users_list:
                st.dataframe(users_list, use_container_width=True)
                st.info(f"📌 Total de usuarios registrados: {len(users_list)}")
            else:
                st.info("No hay usuarios registrados en la base de datos.")
        except Exception as e:
            st.error(f"❌ Error al cargar usuarios: {str(e)}")
