import os
import streamlit as st
import requests

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

# Configuración de URLs
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1")
TICKETS_URL = f"{API_BASE_URL}/tickets/"
USERS_URL = f"{API_BASE_URL}/users/"

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
            
            payload = {
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
                response = requests.post(TICKETS_URL, json=payload)
                if response.status_code == 201:
                    ticket_creado = response.json()
                    st.success(f"✅ Ticket creado exitosamente con ID: {ticket_creado['id']}")
                    st.balloons()
                else:
                    st.error(f"❌ Error al crear el ticket. Código: {response.status_code}")
                    st.json(response.json())
            except requests.exceptions.ConnectionError:
                st.error("🚨 No se pudo conectar con el Backend. Asegúrese de que FastAPI esté en ejecución.")

# ============================================
# PESTAÑA 2: HISTORIAL DE TICKETS
# ============================================
with tab2:
    st.header("📊 Historial y Respaldo de Tickets")
    st.write("Visualización directa de la base de datos para auditoría y migración.")
    
    if st.button("🔄 Actualizar Historial", key="btn_historial"):
        try:
            response_get = requests.get(TICKETS_URL)
            if response_get.status_code == 200:
                tickets_data = response_get.json()
                if tickets_data:
                    st.dataframe(tickets_data, use_container_width=True)
                    st.info(f"📌 Total de tickets registrados: {len(tickets_data)}")
                else:
                    st.info("La base de datos está conectada, pero aún no hay tickets registrados.")
            else:
                st.error(f"Error al consultar la base de datos. Código: {response_get.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("🚨 No se pudo conectar con el Backend para recuperar el historial.")

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
                user_payload = {
                    "email": email,
                    "full_name": full_name,
                    "department": department,
                    "role": role
                }
                
                try:
                    response = requests.post(USERS_URL, json=user_payload)
                    if response.status_code == 201:
                        user_creado = response.json()
                        st.success(f"✅ Usuario registrado exitosamente con ID: {user_creado['id']}")
                        st.balloons()
                    else:
                        st.error(f"❌ Error al registrar el usuario. Código: {response.status_code}")
                        st.json(response.json())
                except requests.exceptions.ConnectionError:
                    st.error("🚨 No se pudo conectar con el Backend. Asegúrese de que FastAPI esté en ejecución.")
    
    st.markdown("---")
    
    # Sección: Listar usuarios registrados
    st.subheader("📋 Usuarios Registrados")
    
if st.button("Actualizar Historial"):
    try:
        response_get = requests.get(f"{API_BASE_URL}/tickets/")
        if response_get.status_code == 200:
            tickets_data = response_get.json()
            if tickets_data:
                # --- NUEVO: Panel de Métricas ---
                total_tickets = len(tickets_data)
                total_incidentes = sum(1 for t in tickets_data if t.get("type") == "Incidente")
                total_req = sum(1 for t in tickets_data if t.get("type") == "Requerimiento")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Tickets", total_tickets)
                col2.metric("Incidentes", total_incidentes)
                col3.metric("Requerimientos", total_req)
                st.markdown("---")
                
                # Despliegue de la tabla
                st.dataframe(tickets_data, use_container_width=True)
            else:
                st.info("La base de datos está conectada, pero aún no hay tickets registrados.")
        else:
            st.error(f"Error al consultar la base de datos. Código: {response_get.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("🚨 No se pudo conectar con el Backend para recuperar el historial.")
