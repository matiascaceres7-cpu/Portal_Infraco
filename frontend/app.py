import os
import smtplib
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from email.mime.text import MIMEText

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
        
        # Construir asunto
        asunto = f"NUEVO TICKET [Urgencia: {ticket_data['urgency']}] - {ticket_data['subject']}"
        
        # Construir cuerpo en texto plano con formato ServiceDesk (@@campo: valor@@)
        cuerpo_texto = f"""NUEVO TICKET CREADO EN EL PORTAL DE SERVICIOS TI
{'='*60}

@@ID_TICKET: {ticket_id}@@
@@Empresa: {ticket_data['account']}@@
@@Ubicacion: {ticket_data['site']}@@
@@Nivel: {ticket_data['level']}@@
@@Tipo: {ticket_data['type']}@@
@@Categoria: {ticket_data['category']}@@
@@Subcategoria: {ticket_data['subcategory']}@@
@@Elemento_Afectado: {ticket_data['item']}@@
@@Prioridad: {ticket_data['priority']}@@
@@Urgencia: {ticket_data['urgency']}@@
@@Asunto: {ticket_data['subject']}@@

DESCRIPCIÓN DEL INCIDENTE:
{'='*60}
{ticket_data['description']}

{'='*60}
Este es un correo automático generado por el Portal de Servicios TI.
Por favor, no responda directamente a este correo.
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

# Mapeo de prioridad y urgencia (español -> inglés)
PRIORITY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}
URGENCY_MAP = {"Baja": "Low", "Media": "Medium", "Alta": "High"}

# Categorías estándar de infraestructura
CATEGORIAS = ["Network", "Hardware", "Software", "Accesos", "Telefonía", "Servidores"]

# Crear las tres pestañas principales
tab1, tab2, tab3 = st.tabs(["Generar Ticket", "Historial de Tickets", "Gestión de Usuarios"])

# ============================================
# PESTAÑA 1: GENERAR TICKET (MODULAR CON TABS)
# ============================================
with tab1:
    st.header("📝 Generación de Tickets")
    st.write("Complete los parámetros del ticket (Estándar ManageEngine)")
    
    # Crear tabs para Incidente y Requerimiento
    tab_incidente, tab_requerimiento = st.tabs(["Incidente", "Requerimiento"])
    
    # ============================================
    # SUB-TAB: INCIDENTE
    # ============================================
    with tab_incidente:
        # Banner de Incidente (placeholder)
        st.image("https://via.placeholder.com/800x150?text=Banner+Incidente", use_column_width=True)
        
        st.subheader("📌 Formulario de Incidente")
        
        with st.form("ticket_form_incidente"):
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                empresa = st.text_input("Empresa", value="On NetFibra", disabled=True, key="empresa_incidente")
                ubicacion = st.selectbox("Ubicación", ["Piso 14", "Piso 15", "Remoto"], key="ubicacion_incidente")
                categoria = st.selectbox("Categoría", CATEGORIAS, key="categoria_incidente")
                subcategoria = st.text_input("Subcategoría", value="", key="subcategoria_incidente")
            
            with col2:
                nivel = st.selectbox("Nivel", ["Nivel 1", "Nivel 2"], key="nivel_incidente")
                prioridad_es = st.selectbox("Prioridad", ["Baja", "Media", "Alta"], key="prioridad_incidente")
                urgencia_es = st.selectbox("Urgencia", ["Baja", "Media", "Alta"], key="urgencia_incidente")
                elemento = st.text_input("Elemento Afectado", value="", key="elemento_incidente")
            
            st.markdown("---")
            asunto = st.text_input("Asunto", value="", key="asunto_incidente")
            descripcion = st.text_area("Descripción Detallada", placeholder="Ingrese los detalles del incidente...", key="descripcion_incidente")
            
            submitted = st.form_submit_button("✅ Crear Incidente")
            
            if submitted:
                # Validación de campos obligatorios
                if not asunto or not descripcion:
                    st.error("❌ Asunto y Descripción son campos obligatorios.")
                else:
                    # Mapeo de prioridad y urgencia a inglés
                    prioridad = PRIORITY_MAP[prioridad_es]
                    urgencia = URGENCY_MAP[urgencia_es]
                    
                    ticket_data = {
                        "type": "Incidente",
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
                        ticket_id = doc_ref[1].id
                        
                        st.success(f"✅ Incidente creado exitosamente con ID: {ticket_id}")
                        
                        # Enviar correo técnico de notificación
                        email_enviado = enviar_correo_tecnico(ticket_data, ticket_id)
                        
                        if email_enviado:
                            st.info("📧 Notificación enviada al equipo técnico.")
                        
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al crear el incidente: {str(e)}")
    
    # ============================================
    # SUB-TAB: REQUERIMIENTO
    # ============================================
    with tab_requerimiento:
        # Banner de Requerimiento (placeholder)
        st.image("https://via.placeholder.com/800x150?text=Banner+Requerimiento", use_column_width=True)
        
        st.subheader("📌 Formulario de Requerimiento")
        
        with st.form("ticket_form_requerimiento"):
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                empresa = st.text_input("Empresa", value="On NetFibra", disabled=True, key="empresa_requerimiento")
                ubicacion = st.selectbox("Ubicación", ["Piso 14", "Piso 15", "Remoto"], key="ubicacion_requerimiento")
                categoria = st.selectbox("Categoría", CATEGORIAS, key="categoria_requerimiento")
                subcategoria = st.text_input("Subcategoría", value="", key="subcategoria_requerimiento")
            
            with col2:
                nivel = st.selectbox("Nivel", ["Nivel 1", "Nivel 2"], key="nivel_requerimiento")
                prioridad_es = st.selectbox("Prioridad", ["Baja", "Media", "Alta"], key="prioridad_requerimiento")
                urgencia_es = st.selectbox("Urgencia", ["Baja", "Media", "Alta"], key="urgencia_requerimiento")
                elemento = st.text_input("Elemento Afectado", value="", key="elemento_requerimiento")
            
            st.markdown("---")
            asunto = st.text_input("Asunto", value="", key="asunto_requerimiento")
            descripcion = st.text_area("Descripción Detallada", placeholder="Ingrese los detalles del requerimiento...", key="descripcion_requerimiento")
            
            submitted = st.form_submit_button("✅ Crear Requerimiento")
            
            if submitted:
                # Validación de campos obligatorios
                if not asunto or not descripcion:
                    st.error("❌ Asunto y Descripción son campos obligatorios.")
                else:
                    # Mapeo de prioridad y urgencia a inglés
                    prioridad = PRIORITY_MAP[prioridad_es]
                    urgencia = URGENCY_MAP[urgencia_es]
                    
                    ticket_data = {
                        "type": "Requerimiento",
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
                        ticket_id = doc_ref[1].id
                        
                        st.success(f"✅ Requerimiento creado exitosamente con ID: {ticket_id}")
                        
                        # Enviar correo técnico de notificación
                        email_enviado = enviar_correo_tecnico(ticket_data, ticket_id)
                        
                        if email_enviado:
                            st.info("📧 Notificación enviada al equipo técnico.")
                        
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al crear el requerimiento: {str(e)}")

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
