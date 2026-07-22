import os
import smtplib
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Portal de Servicios Infraco", page_icon="🔧", layout="wide")

# --- CSS Personalizado para tema corporativo limpio ---
css_personalizado = """
<style>
    /* Fondo general claro */
    * {
        margin: 0;
        padding: 0;
    }
    
    [data-testid="stMainBlockContainer"] {
        background-color: #f5f5f5;
        padding: 0;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #f5f5f5;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Tarjetas de contenedor */
    [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Botones estilizados */
    button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Inputs y selectbox */
    input, select, textarea {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: #0052a3 !important;
        box-shadow: 0 0 0 2px rgba(0, 82, 163, 0.1) !important;
    }
    
    /* Títulos y textos */
    h1, h2, h3 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
    }
    
    p, label, div {
        color: #404040 !important;
    }
    
    /* Métrica */
    [data-testid="metric-container"] {
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #efefef;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 8px !important;
        border: 1px solid #efefef !important;
    }
</style>
"""

st.markdown(css_personalizado, unsafe_allow_html=True)

# --- Banner Principal Corporativo ---
banner_html = """
<div style="
    background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%);
    padding: 40px 20px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 4px 12px rgba(0, 82, 163, 0.15);
    text-align: center;
">
    <h1 style="color: white; margin-bottom: 10px; font-size: 2.5em;">
        ¡Bienvenido al Portal de Servicios Infraco!
    </h1>
    <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.1em; margin: 0;">
        Genera tickets para Incidentes y Requerimientos de forma rápida y segura
    </p>
</div>
"""

st.markdown(banner_html, unsafe_allow_html=True)

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
        # Obtener configuración de correo desde st.secrets
        email_config = st.secrets["email"]
        
        # Datos necesarios del correo
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
        
        # Crear mensaje MIME en texto plano
        mensaje = MIMEText(cuerpo_texto, 'plain', 'utf-8')
        mensaje['Subject'] = asunto
        mensaje['From'] = sender_email
        mensaje['To'] = recipient_email
        
        # Conectar a servidor SMTP y enviar
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
# LAYOUT PRINCIPAL CON COLUMNAS
# ============================================
col_principal, col_lateral = st.columns([7, 3])

# ============================================
# PANEL LATERAL: MIS ELEMENTOS ACTIVOS
# ============================================
with col_lateral:
    st.markdown("### 📊 Mis elementos activos")
    
    try:
        # Contar tickets totales
        tickets_total = 0
        for doc in db.collection('tickets').stream():
            tickets_total += 1
        
        st.metric(label="Solicitudes Totales", value=tickets_total)
        
        # Mostrar estado del sistema
        st.markdown("---")
        st.markdown("#### Estado del Sistema")
        st.success("✅ Firestore conectado")
        st.success("✅ Email configurado")
        
    except Exception as e:
        st.error(f"⚠️ Error al consultar: {str(e)}")

# ============================================
# PANEL PRINCIPAL: FORMULARIO Y TARJETAS
# ============================================
with col_principal:
    
    # Si no hay vista seleccionada, mostrar tarjetas de selección
    if st.session_state.vista_actual is None:
        st.markdown("### Selecciona el tipo de solicitud")
        
        col_incidente, col_req = st.columns(2)
        
        with col_incidente:
            if st.button(
                "📄 INCIDENTE\n\nReportar una falla o problema\nque requiere atención inmediata",
                use_container_width=True,
                key="btn_incidente"
            ):
                st.session_state.vista_actual = "Incidente"
                st.rerun()
        
        with col_req:
            if st.button(
                "📝 REQUERIMIENTO\n\nSolicitar un nuevo servicio\no mejora del sistema",
                use_container_width=True,
                key="btn_requerimiento"
            ):
                st.session_state.vista_actual = "Requerimiento"
                st.rerun()
    
    # Si hay vista seleccionada, mostrar formulario
    else:
        tipo_selected = st.session_state.vista_actual
        
        # Botón para volver
        if st.button("← Volver a seleccionar tipo", use_container_width=False):
            st.session_state.vista_actual = None
            st.rerun()
        
        st.markdown(f"### Nuevo {tipo_selected}")
        st.markdown("Completa los campos para crear tu solicitud")
        st.markdown("---")
        
        # Formulario dinámico
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
            
            # Segunda fila
            subcategoria = st.text_input(
                "Subcategoría",
                placeholder="Ej: WiFi, Base de datos, Conectividad",
                key=f"subcategoria_{tipo_selected}"
            )
            
            elemento = st.text_input(
                "Elemento Afectado",
                placeholder="Ej: Switch de Piso 14, Servidor DB-001",
                key=f"elemento_{tipo_selected}"
            )
            
            # Tercera fila
            asunto = st.text_input(
                "Asunto",
                placeholder="Título breve del problema o solicitud",
                key=f"asunto_{tipo_selected}"
            )
            
            descripcion = st.text_area(
                "Descripción Detallada",
                placeholder="Describe con detalle el problema, pasos reproducibles, o detalles de la solicitud...",
                height=150,
                key=f"descripcion_{tipo_selected}"
            )
            
            st.markdown("---")
            
            # Botones de acción
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submitted = st.form_submit_button(
                    f"✅ Enviar {tipo_selected}",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_btn2:
                st.form_submit_button(
                    "🔄 Limpiar",
                    use_container_width=True,
                    type="secondary"
                )
            
            # Procesar envío
            if submitted:
                # Validación
                if not asunto.strip() or not descripcion.strip():
                    st.error("❌ Asunto y Descripción son campos obligatorios.")
                else:
                    # Mapeo de prioridad y urgencia
                    prioridad = PRIORITY_MAP[prioridad_es]
                    urgencia = URGENCY_MAP[urgencia_es]
                    
                    # Preparar datos del ticket
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
                        
                        # Mostrar mensajes de éxito
                        st.success(f"✅ {tipo_selected} creado exitosamente")
                        st.info(f"📋 ID del ticket: **{ticket_id}**")
                        
                        if email_enviado:
                            st.success("📧 Notificación enviada al equipo técnico")
                        
                        st.balloons()
                        
                        # Resetear vista después de 3 segundos
                        import time
                        time.sleep(2)
                        st.session_state.vista_actual = None
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al crear el {tipo_selected.lower()}: {str(e)}")

# ============================================
# PESTAÑA DE HISTORIAL Y USUARIOS (FOOTER)
# ============================================
st.markdown("---")

tab_historial, tab_usuarios = st.tabs(["📊 Historial de Tickets", "👥 Gestión de Usuarios"])

# ============================================
# HISTORIAL DE TICKETS
# ============================================
with tab_historial:
    st.markdown("### Historial y Respaldo de Tickets")
    st.markdown("Visualización directa de la base de datos para auditoría y migración.")
    
    if st.button("🔄 Actualizar Historial", key="btn_historial"):
        try:
            tickets_list = []
            for doc in db.collection('tickets').stream():
                ticket_dict = doc.to_dict()
                ticket_dict['id'] = doc.id
                tickets_list.append(ticket_dict)
            
            if tickets_list:
                # Métricas
                total_tickets = len(tickets_list)
                total_incidentes = sum(1 for t in tickets_list if t.get("type") == "Incidente")
                total_req = sum(1 for t in tickets_list if t.get("type") == "Requerimiento")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total de Tickets", total_tickets)
                col_m2.metric("Incidentes", total_incidentes)
                col_m3.metric("Requerimientos", total_req)
                
                st.markdown("---")
                st.dataframe(tickets_list, use_container_width=True)
            else:
                st.info("La base de datos está conectada, pero aún no hay tickets registrados.")
        except Exception as e:
            st.error(f"❌ Error al consultar Firestore: {str(e)}")

# ============================================
# GESTIÓN DE USUARIOS
# ============================================
with tab_usuarios:
    st.markdown("### Gestión de Usuarios")
    
    col_reg, col_list = st.columns(2)
    
    with col_reg:
        st.markdown("#### ➕ Registrar Nuevo Usuario")
        
        with st.form("user_form"):
            email = st.text_input("📧 Correo Electrónico", placeholder="usuario@example.com", key="email_user")
            full_name = st.text_input("👤 Nombre Completo", placeholder="Juan Pérez", key="full_name_user")
            department = st.text_input("🏢 Departamento", placeholder="Infraestructura TI", key="department_user")
            role = st.selectbox("🔐 Rol", ["user", "admin", "technician"], key="role_user")
            
            submitted_user = st.form_submit_button("✅ Registrar Usuario", use_container_width=True)
            
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
                        st.success(f"✅ Usuario registrado exitosamente con ID: {doc_ref[1].id}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al registrar el usuario: {str(e)}")
    
    with col_list:
        st.markdown("#### 📋 Usuarios Registrados")
        
        if st.button("🔄 Cargar Usuarios", key="btn_usuarios"):
            try:
                users_list = []
                for doc in db.collection('users').stream():
                    user_dict = doc.to_dict()
                    user_dict['id'] = doc.id
                    users_list.append(user_dict)
                
                if users_list:
                    st.dataframe(users_list, use_container_width=True)
                    st.info(f"📌 Total de usuarios registrados: {len(users_list)}")
                else:
                    st.info("No hay usuarios registrados en la base de datos.")
            except Exception as e:
                st.error(f"❌ Error al cargar usuarios: {str(e)}")
