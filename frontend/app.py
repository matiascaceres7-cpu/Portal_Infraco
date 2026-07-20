import os
import streamlit as st
import requests

st.set_page_config(page_title="IT Service Desk", page_icon="🔧", layout="wide")
st.title("Portal de Servicios TI")
st.subheader("Sistema Integral de Gestión de Tickets y Usuarios")

# Configuración de URLs
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1")
TICKETS_URL = f"{API_BASE_URL}/tickets/"
USERS_URL = f"{API_BASE_URL}/users/"

# Crear las tres pestañas
tab1, tab2, tab3 = st.tabs(["Generar Ticket", "Historial de Tickets", "Gestión de Usuarios"])

# ============================================
# PESTAÑA 1: GENERAR TICKET
# ============================================
with tab1:
    st.header("📝 Generación de Tickets")
    st.write("Complete los parámetros del ticket (Estándar ManageEngine)")
    
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo de Ticket", ["Incidente", "Requerimiento"], key="tipo_ticket")
            account = st.text_input("Account", value="Buk", key="account_ticket")
            site = st.text_input("Site", value="Pisos 14, 15 y 16", key="site_ticket")
            category = st.text_input("Category", value="Network", key="category_ticket")
            subcategory = st.text_input("Subcategory", value="WiFi", key="subcategory_ticket")
        
        with col2:
            level = st.selectbox("Level", ["Tier 1", "Tier 2", "Tier 3"], key="level_ticket")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="priority_ticket")
            urgency = st.selectbox("Urgency", ["Low", "Medium", "High"], key="urgency_ticket")
            item = st.text_input("Item", value="Cortes de señal y zonas de sombra", key="item_ticket")
        
        st.markdown("---")
        subject = st.text_input("Asunto (Subject)", value="Diagnóstico y optimización de red WiFi", key="subject_ticket")
        description = st.text_area("Descripción detallada", placeholder="Ingrese los detalles del requerimiento o incidente...", key="description_ticket")
        
        submitted = st.form_submit_button("✅ Crear Ticket")
        
        if submitted:
            payload = {
                "type": tipo,
                "account": account,
                "site": site,
                "category": category,
                "subcategory": subcategory,
                "item": item,
                "level": level,
                "priority": priority,
                "urgency": urgency,
                "subject": subject,
                "description": description
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
    
    if st.button("📲 Listar Usuarios Registrados", key="btn_users"):
        try:
            response_get = requests.get(USERS_URL)
            if response_get.status_code == 200:
                users_data = response_get.json()
                if users_data:
                    st.dataframe(users_data, use_container_width=True)
                    st.info(f"📌 Total de usuarios registrados: {len(users_data)}")
                else:
                    st.info("La base de datos está conectada, pero aún no hay usuarios registrados.")
            else:
                st.error(f"Error al consultar la base de datos. Código: {response_get.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("🚨 No se pudo conectar con el Backend para recuperar el listado de usuarios.")
