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
st.set_page_config(page_title="Portal de Servicios On NetFibra", page_icon="🔧", layout="wide")

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

# Diccionario de Categorías y Subcategorías dinámicas (Nivel 1 - Helpdesk)
categorias_dict = {
    "Instalación de Software / Aplicaciones": [
        "Solicitar instalación de software con restricción (Ej: Project, Visio)",
        "Actualización de un programa",
        "Otro"
    ],
    "Impresoras / Multifuncionales": [
        "Atasco de papel",
        "Sin conexión / No imprime",
        "Cambio de tóner",
        "Manchas en la impresión",
        "Otro"
    ],
    "Cámaras web / Videollamadas": [
        "No da imagen",
        "Micrófono no funciona",
        "Aplicación (Teams/Zoom) no la reconoce",
        "Otro"
    ],
    "Estaciones de Trabajo (PCs)": [
        "Lentitud en el sistema",
        "No enciende",
        "Pantalla azul",
        "Otro"
    ],
    "Redes y Conectividad": [
        "Sin acceso a Internet",
        "Corte de señal WiFi",
        "Punto de red físico dañado",
        "Otro"
    ],
    "Otro": ["Otro"]
}

CATEGORIAS = list(categorias_dict.keys())

# Plantillas de Descripción Simplificadas (Sin tecnicismos)
PLANTILLA_INCIDENTE = """¿Qué equipo te está fallando? (Ej: Mi notebook, la impresora del pasillo):

¿Dónde estás ubicado? (Ej: Piso 3, Oficina de Finanzas):

Describe el problema detalladamente:"""

PLANTILLA_REQUERIMIENTO = """¿Qué necesitas que hagamos?:

¿Para cuándo lo necesitas?:

Justificación de la solicitud:"""

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
        ¡Bienvenido al Portal de Servicios On NetFibra!
    </h1>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# ============================================
# LAYOUT CENTRADO: TARJETAS CON IMÁGENES Y BOTONES
# ============================================

# Si no hay vista seleccionada, mostrar tarjetas
if st.session_state.vista_actual is None:
    st.markdown("### Selecciona el tipo de solicitud")
    
    col_vacia1, col_incidente, col_req, col_vacia2 = st.columns([1, 2, 2, 1])
    
    # ============================================
    # TARJETA INCIDENTE (centrada)
    # ============================================
    with col_incidente:
        # Intentar cargar imagen de incidente
        try:
            st.image("frontend/banner_incidente.png", use_container_width=True)
        except FileNotFoundError:
            st.info("ℹ️ Imagen de incidente no disponible")
        
        # Botón debajo de la imagen
        if st.button(
            "📄 INCIDENTE",
            use_container_width=True,
            key="btn_incidente"
        ):
            st.session_state.vista_actual = "Incidente"
            st.rerun()
    
    # ============================================
    # TARJETA REQUERIMIENTO (centrada)
    # ============================================
    with col_req:
        # Intentar cargar imagen de requerimiento
        try:
            st.image("frontend/banner_requerimiento.png", use_container_width=True)
        except FileNotFoundError:
            st.info("ℹ️ Imagen de requerimiento no disponible")
        
        # Botón debajo de la imagen
        if st.button(
            "📝 REQUERIMIENTO",
            use_container_width=True,
            key="btn_requerimiento"
        ):
            st.session_state.vista_actual = "Requerimiento"
            st.rerun()

# ============================================
# SECCIÓN DE FORMULARIO (cuando se selecciona tipo)
# ============================================
else:
    tipo_selected = st.session_state.vista_actual
    
    # Botón para volver
    if st.button("← Volver", use_container_width=False):
        st.session_state.vista_actual = None
        st.rerun()
    
    st.markdown(f"### {tipo_selected}")
    st.markdown("---")
    
    # Determinar plantilla según tipo
    if tipo_selected == "Incidente":
        plantilla_descripcion = PLANTILLA_INCIDENTE
    else:
        plantilla_descripcion = PLANTILLA_REQUERIMIENTO
    
    # ============================================
    # CAMPOS FUERA DE st.form PARA DINÁMICA EN TIEMPO REAL
    # ============================================
    
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
        # Categoria con subcategorías dinámicas (FUERA DE FORM)
        categoria_seleccionada = st.selectbox(
            "Categoría",
            CATEGORIAS,
            key=f"categoria_{tipo_selected}"
        )
        
        # Si elige "Otro" en categoría, mostrar campo de texto libre
        if categoria_seleccionada == "Otro":
            categoria_final = st.text_input(
                "Especifique la Categoría",
                placeholder="Ingrese la categoría",
                key=f"categoria_otro_{tipo_selected}"
            )
        else:
            categoria_final = categoria_seleccionada
    
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
    
    # Subcategoría dinámica según categoría seleccionada (FUERA DE FORM)
    subcategorias_disponibles = categorias_dict.get(categoria_seleccionada, ["Otro"])
    subcategoria_seleccionada = st.selectbox(
        "Subcategoría",
        subcategorias_disponibles,
        key=f"subcategoria_{tipo_selected}"
    )
    
    # Si elige "Otro" en subcategoría, mostrar campo de texto libre
    if subcategoria_seleccionada == "Otro":
        subcategoria_final = st.text_input(
            "Especifique la Subcategoría",
            placeholder="Ingrese la subcategoría",
            key=f"subcategoria_otro_{tipo_selected}"
        )
    else:
        subcategoria_final = subcategoria_seleccionada
    
    # Elemento Afectado
    elemento = st.text_input(
        "Elemento Afectado",
        placeholder="Ej: Mi notebook, la impresora del pasillo, el router",
        key=f"elemento_{tipo_selected}"
    )
    
    # Asunto
    asunto = st.text_input(
        "Asunto",
        placeholder="Título breve del problema o solicitud",
        key=f"asunto_{tipo_selected}"
    )
    
    # Descripción con plantilla dinámica
    descripcion = st.text_area(
        "Descripción Detallada",
        value=plantilla_descripcion,
        height=200,
        key=f"descripcion_{tipo_selected}"
    )
    
    st.markdown("---")
    
    # ============================================
    # BOTÓN ENVIAR FUERA DE FORM (Para permitir dinámica)
    # ============================================
    
    if st.button(
        f"✅ Enviar {tipo_selected}",
        use_container_width=True,
        type="primary",
        key=f"btn_enviar_{tipo_selected}"
    ):
        # Validación de campos obligatorios
        if not asunto.strip() or not descripcion.strip():
            st.error("❌ Asunto y Descripción son campos obligatorios.")
        # Validar que categoria_final y subcategoria_final no estén vacías si eligió "Otro"
        elif categoria_seleccionada == "Otro" and not categoria_final.strip():
            st.error("❌ Debe especificar la categoría.")
        elif subcategoria_seleccionada == "Otro" and not subcategoria_final.strip():
            st.error("❌ Debe especificar la subcategoría.")
        else:
            prioridad = PRIORITY_MAP[prioridad_es]
            urgencia = URGENCY_MAP[urgencia_es]
            
            ticket_data = {
                "type": tipo_selected,
                "account": empresa,
                "site": ubicacion,
                "category": categoria_final,  # Variable final con "Otro" resuelto
                "subcategory": subcategoria_final,  # Variable final con "Otro" resuelto
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
