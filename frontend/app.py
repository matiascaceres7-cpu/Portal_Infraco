import os
import smtplib
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from email.mime.text import MIMEText
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(page_title="Portal de Servicios Infraco", page_icon="🔧", layout="wide")

# ============================================
# CONEXIÓN A FIRESTORE
# ============================================
@st.cache_resource
def get_firestore_client():
    """Inicializa y retorna el cliente de Firestore usando las credenciales de st.secrets"""
    try:
        credentials_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        db = firestore.Client(credentials=credentials, project=credentials.project_id)
        return db
    except KeyError:
        st.error("❌ No se encontraron las credenciales de GCP en st.secrets. Configure 'gcp_service_account'.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error al conectar con Firestore: {str(e)}")
        st.stop()

db = get_firestore_client()

# ============================================
# FUNCIÓN PARA ENVÍO DE CORREOS TRANSACCIONALES
# ============================================
def enviar_correo_tecnico(ticket_data, ticket_id):
    """
    Envía un correo electrónico transaccional al equipo técnico con los detalles del ticket.
    Formato ServiceDesk con etiquetas @@ para parseo automático.
    
    Args:
        ticket_data (dict): Diccionario con los datos del ticket
        ticket_id (str): ID único del documento del ticket en Firestore
    """
    try:
        email_config = st.secrets["email"]
        sender_email = email_config["sender"]
        sender_password = email_config["password"]
        recipient_email = email_config["recipient_tech"]
        smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
        smtp_port = email_config.get("smtp_port", 465)
        
        # Construir asunto con formato ServiceDesk (contiene "Solicitud")
        tipo_ticket = ticket_data['type']
        asunto = f"Solicitud - {tipo_ticket} - {ticket_data['subject']}"
        
        # Construir cuerpo en texto plano con formato ServiceDesk (@@CAMPO=VALOR@@)
        cuerpo_texto = f"""@@ACCOUNT={ticket_data['account']}@@
@@SITE={ticket_data['site']}@@
@@OPERATION=AddRequest@@
@@CATEGORY={ticket_data['category']}@@
@@SUBCATEGORY={ticket_data['subcategory']}@@
@@ITEM={ticket_data['item']}@@
@@LEVEL={ticket_data['level']}@@
@@MODE=Web Form@@
@@PRIORITY={ticket_data['priority']}@@
@@URGENCY={ticket_data['urgency']}@@


{ticket_data['description']}
"""
        
        mensaje = MIMEText(cuerpo_texto, 'plain', 'utf-8')
        mensaje['Subject'] = asunto
        mensaje['From'] = sender_email
        mensaje['To'] = recipient_email
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(mensaje)
        
        return True
    
    except KeyError as ke:
        st.warning(f"⚠️ Configuración de correo incompleta. Falta: {str(ke)}. El ticket fue creado pero no se envió notificación.")
        return False
    except smtplib.SMTPAuthenticationError:
        st.warning("⚠️ Error de autenticación SMTP. Verifica las credenciales de correo en st.secrets. El ticket fue creado.")
        return False
    except smtplib.SMTPException as e:
        st.warning(f"⚠️ Error SMTP al enviar el correo: {str(e)}. El ticket fue creado pero no se notificó.")
        return False
    except Exception as e:
        st.warning(f"⚠️ Error al enviar correo transaccional: {str(e)}. El ticket fue creado correctamente.")
        return False

# ============================================
# CONFIGURACIONES Y MAPEOS
# ============================================
PRIORITY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}
URGENCY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}
CATEGORIAS = ["Network", "Hardware", "Software", "Accesos", "Telefonía", "Servidores"]

# Inicializar estado de sesión
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = None

# ============================================
# BANNER PRINCIPAL (ROJO)
# ============================================
banner_html = """
<div style="
    background-color: #c41e3a;
    padding: 30px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
">
    <h1 style="color: white; margin: 0; font-size: 2.2em; font-weight: bold;">
        Portal de Servicios Infraco
    </h1>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# ============================================
# LAYOUT PRINCIPAL: DOS COLUMNAS
# ============================================
col_principal, col_lateral = st.columns([7, 3])

# ============================================
# COLUMNA LATERAL (3): TICKETS ACTIVOS
# ============================================
with col_lateral:
    st.markdown("### 📊 Tickets Activos")
    
    try:
        # Contar tickets totales desde Firestore
        total_tickets = 0
        for doc in db.collection('tickets').stream():
            total_tickets += 1
        
        st.metric(label="Total de Solicitudes", value=total_tickets)
        
    except Exception as e:
        st.warning(f"⚠️ Error al consultar: {str(e)}")

# ============================================
# COLUMNA PRINCIPAL (7): FORMULARIO
# ============================================
with col_principal:
    
    # Si no hay vista seleccionada, mostrar botones
    if st.session_state.vista_actual is None:
        st.markdown("### Selecciona el tipo de solicitud")
        
        col_incidente, col_requerimiento = st.columns(2)
        
        with col_incidente:
            if st.button(
                "📄 INCIDENTE",
                use_container_width=True,
                key="btn_incidente"
            ):
                st.session_state.vista_actual = "Incidente"
                st.rerun()
        
        with col_requerimiento:
            if st.button(
                "📝 REQUERIMIENTO",
                use_container_width=True,
                key="btn_requerimiento"
            ):
                st.session_state.vista_actual = "Requerimiento"
                st.rerun()
    
    # Si hay vista seleccionada, mostrar formulario
    else:
        tipo_selected = st.session_state.vista_actual
        
        # Botón para volver
        if st.button("← Volver", use_container_width=False):
            st.session_state.vista_actual = None
            st.rerun()
        
        st.markdown(f"### {tipo_selected}")
        
        # Intentar cargar imagen de banner
        if tipo_selected == "Incidente":
            banner_path = "frontend/banner_incidente.png"
        else:
            banner_path = "frontend/banner_requerimiento.png"
        
        try:
            st.image(banner_path, use_column_width=True)
        except FileNotFoundError:
            st.info(f"ℹ️ Imagen de banner no encontrada: {banner_path}")
        
        st.markdown("---")
        
        # Formulario
        with st.form(f"form_{tipo_selected.lower()}"):
            
            # Primera fila
            col1, col2 = st.columns(2)
            
            with col1:
                empresa = st.text_input(
                    "Empresa",
                    value="On NetFibra",
                    disabled=True,
                    key=f"empresa_{tipo_selected}"
                )
                ubicacion = st.selectbox(
                    "Ubicación",
                    ["Piso 14", "Piso 15", "Remoto"],
                    key=f"ubicacion_{tipo_selected}"
                )
                categoria = st.selectbox(
                    "Categoría",
                    CATEGORIAS,
                    key=f"categoria_{tipo_selected}"
                )
                subcategoria = st.text_input(
                    "Subcategoría",
                    placeholder="Ej: WiFi, Base de datos",
                    key=f"subcategoria_{tipo_selected}"
                )
            
            with col2:
                nivel = st.selectbox(
                    "Nivel",
                    ["Tier 1", "Tier 2"],
                    key=f"nivel_{tipo_selected}"
                )
                prioridad_es = st.selectbox(
                    "Prioridad",
                    ["Baja", "Media", "Alta"],
                    key=f"prioridad_{tipo_selected}"
                )
                urgencia_es = st.selectbox(
                    "Urgencia",
                    ["Baja", "Media", "Alta"],
                    key=f"urgencia_{tipo_selected}"
                )
                elemento = st.text_input(
                    "Elemento Afectado",
                    placeholder="Ej: Switch, Servidor",
                    key=f"elemento_{tipo_selected}"
                )
            
            # Asunto y descripción
            asunto = st.text_input(
                "Asunto",
                placeholder="Título breve",
                key=f"asunto_{tipo_selected}"
            )
            
            descripcion = st.text_area(
                "Descripción Detallada",
                placeholder="Describe el problema o solicitud...",
                height=150,
                key=f"descripcion_{tipo_selected}"
            )
            
            st.markdown("---")
            
            # Botón de envío
            submitted = st.form_submit_button(
                f"✅ Enviar {tipo_selected}",
                use_container_width=True,
                type="primary"
            )
            
            # Procesar envío
            if submitted:
                if not asunto.strip() or not descripcion.strip():
                    st.error("❌ Asunto y Descripción son campos obligatorios.")
                else:
                    prioridad = PRIORITY_MAP[prioridad_es]
                    urgencia = URGENCY_MAP[urgencia_es]
                    
                    ticket_data = {
                        "type": tipo_selected,
                        "account": empresa,
                        "site": ubicacion,
                        "category": categoria,
                        "subcategory": subcategoria,
                        "item": elemento,
                        "level": nivel,
                        "priority": prioridad,
                        "urgency": urgencia,
                        "subject": asunto,
                        "description": descripcion,
                        "created_at": datetime.now()
                    }
                    
                    try:
                        # Guardar en Firestore
                        doc_ref = db.collection('tickets').add(ticket_data)
                        ticket_id = doc_ref[1].id
                        
                        # Enviar correo técnico
                        email_enviado = enviar_correo_tecnico(ticket_data, ticket_id)
                        
                        # Mensajes de éxito
                        st.success(f"✅ {tipo_selected} creado exitosamente")
                        st.info(f"📋 ID del ticket: **{ticket_id}**")
                        
                        if email_enviado:
                            st.success("📧 Notificación enviada al equipo técnico")
                        
                        st.balloons()
                        
                        # Resetear vista
                        import time
                        time.sleep(2)
                        st.session_state.vista_actual = None
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al crear el {tipo_selected.lower()}: {str(e)}")

# ============================================
# FOOTER: TABS DE HISTORIAL Y USUARIOS
# ============================================
st.markdown("---")

tab_historial, tab_usuarios = st.tabs(["📊 Historial de Tickets", "👥 Gestión de Usuarios"])

# ============================================
# TAB: HISTORIAL DE TICKETS
# ============================================
with tab_historial:
    st.markdown("### Historial de Tickets")
    
    if st.button("🔄 Actualizar", key="btn_historial"):
        try:
            tickets_list = []
            for doc in db.collection('tickets').stream():
                ticket_dict = doc.to_dict()
                ticket_dict['id'] = doc.id
                tickets_list.append(ticket_dict)
            
            if tickets_list:
                total_tickets = len(tickets_list)
                total_incidentes = sum(1 for t in tickets_list if t.get("type") == "Incidente")
                total_req = sum(1 for t in tickets_list if t.get("type") == "Requerimiento")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total", total_tickets)
                col_m2.metric("Incidentes", total_incidentes)
                col_m3.metric("Requerimientos", total_req)
                
                st.markdown("---")
                st.dataframe(tickets_list, use_container_width=True)
            else:
                st.info("No hay tickets registrados.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================
# TAB: GESTIÓN DE USUARIOS
# ============================================
with tab_usuarios:
    st.markdown("### Gestión de Usuarios")
    
    col_reg, col_list = st.columns(2)
    
    with col_reg:
        st.markdown("#### Registrar Nuevo Usuario")
        
        with st.form("user_form"):
            email = st.text_input("📧 Correo Electrónico")
            full_name = st.text_input("👤 Nombre Completo")
            department = st.text_input("🏢 Departamento")
            role = st.selectbox("🔐 Rol", ["user", "admin", "technician"])
            
            submitted_user = st.form_submit_button("✅ Registrar", use_container_width=True)
            
            if submitted_user:
                if not email or not full_name or not department:
                    st.error("❌ Todos los campos son obligatorios.")
                else:
                    user_data = {
                        "email": email,
                        "full_name": full_name,
                        "department": department,
                        "role": role,
                        "created_at": datetime.now()
                    }
                    
                    try:
                        doc_ref = db.collection('users').add(user_data)
                        st.success(f"✅ Usuario registrado: {doc_ref[1].id}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col_list:
        st.markdown("#### Usuarios Registrados")
        
        if st.button("🔄 Cargar", key="btn_usuarios"):
            try:
                users_list = []
                for doc in db.collection('users').stream():
                    user_dict = doc.to_dict()
                    user_dict['id'] = doc.id
                    users_list.append(user_dict)
                
                if users_list:
                    st.dataframe(users_list, use_container_width=True)
                    st.info(f"Total: {len(users_list)} usuarios")
                else:
                    st.info("No hay usuarios registrados.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
