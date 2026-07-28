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
# CSS PERSONALIZADO (ESTÉTICA ESTILO SERVICEDESK)
# ============================================
# Nota: algunas reglas apuntan a atributos internos de Streamlit
# (data-testid="stHorizontalBlock", "stVerticalBlockBorderWrapper", "baseButton-*").
# Son estables en versiones recientes, pero si tu versión de Streamlit difiere
# y algún estilo no se aplica, inspecciona el elemento en el navegador y
# ajusta el selector correspondiente.
css_estilo = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

:root{
    --brand-navy:#111c2e;
    --brand-blue:#155eef;
    --brand-red:#c41e3a;
    --brand-green:#128a4f;
    --panel-bg:#eef4ff;
    --panel-border:#cfe0fb;
}

/* ---------- Barra superior tipo ServiceDesk ---------- */
.topbar{
    background:var(--brand-navy);
    padding:14px 26px;
    border-radius:10px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:22px;
    box-shadow:0 4px 14px rgba(0,0,0,0.18);
}
.topbar-brand{
    color:#ffffff;
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:1.2rem;
    display:flex;
    align-items:center;
    gap:10px;
}
.topbar-crumb{
    color:#9fb3d1;
    font-size:0.85rem;
    font-weight:500;
}

/* ---------- Banner principal ---------- */
.hero-banner{
    background:linear-gradient(120deg, var(--brand-red) 0%, #8f1729 100%);
    padding:32px 24px;
    border-radius:14px;
    text-align:center;
    margin-bottom:26px;
    box-shadow:0 8px 22px rgba(196,30,58,0.25);
}
.hero-banner h1{
    color:white;
    margin:0;
    font-family:'Poppins', sans-serif;
    font-size:2em;
    font-weight:700;
}
.hero-banner p{
    color:#ffd9de;
    margin:8px 0 0 0;
    font-size:1rem;
}

/* ---------- Tarjetas de tipo de solicitud ---------- */
.service-card{
    border-radius:16px;
    padding:26px 18px;
    text-align:center;
    color:white;
    min-height:180px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:8px;
    margin-bottom:12px;
    transition:transform .15s ease;
}
.service-card-icon{ font-size:2.3rem; line-height:1; }
.service-card-title{
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:1.1rem;
    letter-spacing:.3px;
}
.service-card-desc{
    font-size:.85rem;
    opacity:.92;
    max-width:230px;
}

/* ---------- Paneles de sección del formulario ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]{
    background:var(--panel-bg) !important;
    border:1px solid var(--panel-border) !important;
    border-radius:14px !important;
}

.section-title{
    font-family:'Poppins', sans-serif;
    font-weight:600;
    font-size:1.05rem;
    color:var(--brand-navy);
    border-bottom:2px solid var(--brand-blue);
    padding-bottom:8px;
    margin-bottom:14px;
    display:flex;
    align-items:center;
    gap:8px;
}

/* ---------- Botones ---------- */
div.stButton > button{
    border-radius:8px !important;
    font-weight:600 !important;
    padding:0.55rem 1.1rem !important;
    border:none !important;
    transition:filter .15s ease;
}
div.stButton > button:hover{ filter:brightness(0.93); }

div.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"]{
    background:var(--brand-blue) !important;
    color:white !important;
}
div.stButton > button[kind="secondary"],
button[data-testid="baseButton-secondary"]{
    background:#eef1f5 !important;
    color:var(--brand-navy) !important;
    border:1px solid #d7dde5 !important;
}

/* Colorea los botones de las tarjetas de inicio según su columna */
div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) div.stButton > button{
    background:var(--brand-red) !important;
    color:white !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-of-type(3) div.stButton > button{
    background:var(--brand-green) !important;
    color:white !important;
}

div[data-testid="stImage"] img{
    height:220px !important;
    object-fit:cover !important;
    border-radius:12px;
}
</style>
"""
st.markdown(css_estilo, unsafe_allow_html=True)

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
    Formato ServiceDesk con etiquetas ## para parseo automático.
    
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
        
        # Construir cuerpo en texto plano con formato ServiceDesk (##CAMPO=VALOR##)
        cuerpo_texto = f"""##ACCOUNT={ticket_data['account']}##
##SITE={ticket_data['site']}##
##OPERATION=AddRequest##
##CATEGORY={ticket_data['category']}##
##SUBCATEGORY={ticket_data['subcategory']}##
##ITEM={ticket_data['item']}##
##LEVEL={ticket_data['level']}##
##MODE=Web Form##
##PRIORITY={ticket_data['priority']}##
##URGENCY={ticket_data['urgency']}##


{ticket_data['description']}
"""
        
        mensaje = MIMEText(cuerpo_texto, 'plain', 'utf-8')
        mensaje['Subject'] = "Solicitud"
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

# Nivel fijo (Tier 1)
NIVEL_FIJO = "Tier 1"

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
# BARRA SUPERIOR
# ============================================
crumb = st.session_state.vista_actual if st.session_state.vista_actual else "Inicio"
st.markdown(f"""
<div class="topbar">
    <div class="topbar-brand">🔧 On NetFibra · Portal de Servicios</div>
    <div class="topbar-crumb">Inicio / {crumb}</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# BANNER PRINCIPAL
# ============================================
banner_html = """
<div class="hero-banner">
    <h1>¡Bienvenido al Portal de Servicios On NetFibra!</h1>
    <p>Reporta incidentes o solicita nuevos requerimientos en un solo lugar.</p>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# ============================================
# LAYOUT CENTRADO: TARJETAS CON ÍCONOS Y BOTONES
# ============================================

def render_service_card(icon, titulo, descripcion, color):
    """Renderiza una tarjeta de tipo de solicitud (reemplaza las imágenes estáticas)."""
    degradados = {
        "rojo": "linear-gradient(135deg, #e6485f 0%, #c41e3a 100%)",
        "verde": "linear-gradient(135deg, #1dbf73 0%, #128a4f 100%)",
    }
    st.markdown(f"""
    <div class="service-card" style="background:{degradados[color]};">
        <div class="service-card-icon">{icon}</div>
        <div class="service-card-title">{titulo}</div>
        <div class="service-card-desc">{descripcion}</div>
    </div>
    """, unsafe_allow_html=True)

# Si no hay vista seleccionada, mostrar tarjetas
if st.session_state.vista_actual is None:
    st.markdown("### Selecciona el tipo de solicitud")
    
    col_vacia1, col_incidente, col_req, col_vacia2 = st.columns([1, 2, 2, 1])
    
    # ============================================
    # TARJETA INCIDENTE (centrada)
    # ============================================
    with col_incidente:
        render_service_card(
            "⚠️",
            "Reportar un Incidente",
            "Algo dejó de funcionar: equipos, impresoras, red o software.",
            "rojo"
        )
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
        render_service_card(
            "📝",
            "Solicitar un Requerimiento",
            "Necesitas algo nuevo: instalaciones, accesos o cambios.",
            "verde"
        )
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
    
    st.markdown(f"### {'⚠️' if tipo_selected == 'Incidente' else '📝'} {tipo_selected}")
    
    # Determinar plantilla según tipo
    if tipo_selected == "Incidente":
        plantilla_descripcion = PLANTILLA_INCIDENTE
    else:
        plantilla_descripcion = PLANTILLA_REQUERIMIENTO
    
    # ============================================
    # PANEL DE DATOS DE LA SOLICITUD
    # CAMPOS FUERA DE st.form PARA DINÁMICA EN TIEMPO REAL
    # ============================================
    panel_datos = st.container(border=True)
    with panel_datos:
        st.markdown('<div class="section-title">🗂️ Datos de la Solicitud</div>', unsafe_allow_html=True)

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

            # Nivel fijo (Tier 1) - No visible para el usuario
            nivel = NIVEL_FIJO

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

    # ============================================
    # PANEL DE DESCRIPCIÓN
    # ============================================
    panel_descripcion = st.container(border=True)
    with panel_descripcion:
        st.markdown('<div class="section-title">🖊️ Descripción de la Solicitud</div>', unsafe_allow_html=True)

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
                "level": nivel,  # Tier 1 fijo
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