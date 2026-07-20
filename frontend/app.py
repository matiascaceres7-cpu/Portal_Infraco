import streamlit as st
import requests

st.set_page_config(page_title="IT Service Desk", page_icon="🔧", layout="centered")
st.title("Portal de Servicios TI")
st.subheader("Generación de Tickets - Formulario Web")

API_URL = "http://127.0.0.1:8000/api/v1/tickets/"

with st.form("ticket_form"):
    st.write("Complete los parámetros del ticket (Estándar ManageEngine)")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox("Tipo de Ticket", ["Incidente", "Requerimiento"])
        account = st.text_input("Account", value="Buk")
        site = st.text_input("Site", value="Pisos 14, 15 y 16")
        category = st.text_input("Category", value="Network")
        subcategory = st.text_input("Subcategory", value="WiFi")
    
    with col2:
        level = st.selectbox("Level", ["Tier 1", "Tier 2", "Tier 3"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        urgency = st.selectbox("Urgency", ["Low", "Medium", "High"])
        item = st.text_input("Item", value="Cortes de señal y zonas de sombra")
    
    st.markdown("---")
    subject = st.text_input("Asunto (Subject)", value="Diagnóstico y optimización de red WiFi")
    description = st.text_area("Descripción detallada", placeholder="Ingrese los detalles del requerimiento o incidente...")
    
    submitted = st.form_submit_button("Crear Ticket")
    
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
            response = requests.post(API_URL, json=payload)
            if response.status_code == 201:
                ticket_creado = response.json()
                st.success(f"✅ Ticket creado exitosamente con ID: {ticket_creado['id']}")
            else:
                st.error(f"❌ Error al crear el ticket. Código: {response.status_code}")
                st.json(response.json())
        except requests.exceptions.ConnectionError:
            st.error("🚨 No se pudo conectar con el Backend. Asegúrese de que FastAPI esté ejecutándose en http://127.0.0.1:8000")
