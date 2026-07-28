"""
streamlit_app.py
------------------
Interfaz web del agente. Este es el archivo que Hugging Face Spaces ejecuta
para levantar la aplicación.
"""

import textwrap

import streamlit as st


def _sin_indentacion(texto: str) -> str:
    """Quita el espacio inicial de cada línea no vacía. Markdown interpreta
    4+ espacios al inicio de una línea como un bloque de código, así que
    cualquier HTML que insertemos vía st.markdown debe ir sin indentación
    para que se renderice como HTML real y no como texto literal.
    textwrap.dedent no basta aquí porque el ícono SVG insertado (multilínea)
    rompe el cálculo del prefijo común."""
    return "\n".join(linea.lstrip() if linea.strip() else "" for linea in texto.split("\n"))


from pathlib import Path

from ingest import construir_indice, CARPETA_DOCUMENTOS
from rag_chain import cargar_cadena_rag, responder_con_fuentes

st.set_page_config(
    page_title="Sonrisa Plena — Asistente virtual",
    page_icon="🦷",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Estilos e identidad visual
# ---------------------------------------------------------------------------
# Paleta: azul-verdoso profundo (texto/marca), teal (acento principal) y un
# coral cálido usado con moderación para el mensaje del paciente — para que
# la interfaz se sienta cuidada y humana, no un chat gris genérico.
ICONO_DIENTE = """
<svg width="34" height="34" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M24 6C17 6 11 9 8 14c-2.5 4-2 9-1 15 1 6 3 13 6.5 13 3 0 3-6 4-10 .6-2.4 1.5-4 6.5-4s5.9 1.6 6.5 4c1 4 1 10 4 10 3.5 0 5.5-7 6.5-13 1-6 1.5-11-1-15-3-5-9-8-16-8Z"
        stroke="#F5F9F8" stroke-width="2.4" stroke-linejoin="round" fill="none"/>
</svg>
"""

st.markdown(
    _sin_indentacion(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Manrope', sans-serif;
    }}

    #MainMenu, footer {{visibility: hidden;}}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    .block-container {{ padding-top: 1rem; max-width: 720px; }}

    /* --- Encabezado de marca --- */
    .spb-header {{
        background: linear-gradient(135deg, #1F6F6B 0%, #12313F 100%);
        border-radius: 18px;
        padding: 22px 26px;
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 22px;
        box-shadow: 0 6px 20px rgba(18, 49, 63, 0.15);
    }}
    .spb-header-text h1 {{
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 1.5rem;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.2;
    }}
    .spb-header-text p {{
        font-family: 'Manrope', sans-serif;
        color: #CDE7E3;
        font-size: 0.88rem;
        margin: 4px 0 0 0;
    }}

    /* --- Burbujas de chat --- */
    [data-testid="stChatMessage"] {{
        border-radius: 14px;
        padding: 4px 6px;
        margin-bottom: 6px;
    }}
    [data-testid="stChatMessageContent"] {{
        font-family: 'Manrope', sans-serif;
        font-size: 0.95rem;
        color: #12313F;
    }}
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{
        background: #FDEEE7;
        border: 1px solid #F6D3C1;
    }}
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {{
        background: #FFFFFF;
        border: 1px solid #DCE7E5;
        border-left: 4px solid #1F6F6B;
    }}

    /* --- Fuentes citadas --- */
    .spb-fuente {{
        display: inline-block;
        font-family: 'Manrope', sans-serif;
        font-size: 0.72rem;
        color: #1F6F6B;
        background: #E6F2F0;
        border: 1px solid #C9E4E0;
        border-radius: 999px;
        padding: 2px 10px;
        margin: 6px 4px 0 0;
    }}

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {{
        background: #FFFFFF;
        border-right: 1px solid #E3EBEA;
    }}
    .spb-sidebar-title {{
        font-family: 'Fraunces', serif;
        font-weight: 600;
        color: #12313F;
        font-size: 1.05rem;
        margin-bottom: 2px;
    }}
    .spb-sidebar-sub {{
        font-family: 'Manrope', sans-serif;
        color: #5C7370;
        font-size: 0.82rem;
        margin-bottom: 14px;
    }}
    .spb-info-card {{
        background: #F5F9F8;
        border: 1px solid #E3EBEA;
        border-radius: 12px;
        padding: 12px 14px;
        font-family: 'Manrope', sans-serif;
        font-size: 0.82rem;
        color: #12313F;
        line-height: 1.6;
        margin-top: 18px;
    }}
    .spb-info-card b {{ color: #1F6F6B; }}
    </style>

    <div class="spb-header">
        {ICONO_DIENTE}
        <div class="spb-header-text">
            <h1>Sonrisa Plena</h1>
            <p>Asistente virtual — resuelve tus dudas sobre citas, precios y privacidad</p>
        </div>
    </div>
    """),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Carga del agente (una sola vez por sesión del servidor)
# ---------------------------------------------------------------------------
@st.cache_resource
def obtener_cadena():
    return cargar_cadena_rag()


try:
    cadena, retriever = obtener_cadena()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar: preguntas rápidas + información de contacto
# ---------------------------------------------------------------------------
PREGUNTAS_RAPIDAS = [
    "¿Cuánto cuesta una limpieza dental?",
    "¿Cómo agendo una cita?",
    "¿Qué hacen con mis datos personales?",
    "¿Atienden los sábados?",
    "¿Qué especialidades ofrecen?",
    "¿Cuánto tiempo antes debo llegar a mi cita?",
]

if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = None

with st.sidebar:
    st.markdown('<p class="spb-sidebar-title">Preguntas frecuentes</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="spb-sidebar-sub">Toca una para enviarla directo al chat</p>',
        unsafe_allow_html=True,
    )
    for pregunta_rapida in PREGUNTAS_RAPIDAS:
        if st.button(pregunta_rapida, use_container_width=True):
            st.session_state.pregunta_pendiente = pregunta_rapida

    st.markdown(
        '<p class="spb-sidebar-title" style="margin-top:22px;">Agregar documentación</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="spb-sidebar-sub">Sube más archivos (.md, .html, .csv, .pdf) para ampliar '
        "lo que el asistente puede responder</p>",
        unsafe_allow_html=True,
    )
    archivos_subidos = st.file_uploader(
        "Subir documentos",
        type=["md", "html", "csv", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if archivos_subidos:
        if st.button("📤 Actualizar base de conocimiento", use_container_width=True):
            with st.spinner("Procesando documentos y reconstruyendo el índice..."):
                CARPETA_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
                for archivo in archivos_subidos:
                    destino = Path(CARPETA_DOCUMENTOS) / archivo.name
                    destino.write_bytes(archivo.getvalue())
                construir_indice()
            obtener_cadena.clear()
            st.success("¡Documentos agregados! La base de conocimiento se actualizó.")
            st.rerun()

    st.markdown(
        textwrap.dedent("""
        <div class="spb-info-card">
            <b>📍 Ubicación</b><br>Av. Insurgentes Sur 1234, Col. Del Valle, CDMX<br><br>
            <b>🕒 Horario</b><br>Lun–Vie 9:00–19:00 · Sáb 9:00–14:00<br><br>
            <b>📞 Contacto</b><br>55 1234 5678
        </div>
        """),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Historial de conversación
# ---------------------------------------------------------------------------
if "historial" not in st.session_state:
    st.session_state.historial = [
        {
            "rol": "assistant",
            "contenido": (
                "¡Hola! Como asistente virtual de Clínica Dental Sonrisa Plena, puedo "
                "ayudarte respondiendo preguntas basadas en nuestra guía de citas y "
                "agendamiento. Me puedes preguntar sobre:\n\n"
                "- Cómo agendar una cita (medios de contacto y ubicación).\n"
                "- Cómo confirmar o consultar tu cita.\n"
                "- Nuestros horarios de atención.\n"
                "- Qué necesitas traer para tu primera cita.\n"
                "- Nuestra política de tolerancia si llegas tarde.\n"
                "- Cómo manejamos las urgencias sin cita previa.\n"
                "- Cómo solicitar un cambio de doctor o especialista.\n\n"
                "¿En qué te puedo ayudar hoy?"
            ),
            "fuentes": ["faq_citas_agendamiento.md"],
        }
    ]

AVATAR_ASISTENTE = "🦷"
AVATAR_USUARIO = "🙂"


def mostrar_fuentes(fuentes):
    if fuentes:
        chips = "".join(f'<span class="spb-fuente">📎 {f}</span>' for f in fuentes)
        st.markdown(chips, unsafe_allow_html=True)


for mensaje in st.session_state.historial:
    avatar = AVATAR_ASISTENTE if mensaje["rol"] == "assistant" else AVATAR_USUARIO
    with st.chat_message(mensaje["rol"], avatar=avatar):
        st.markdown(mensaje["contenido"])
        mostrar_fuentes(mensaje.get("fuentes"))

# ---------------------------------------------------------------------------
# Entrada del usuario (por chat o por chip de pregunta rápida)
# ---------------------------------------------------------------------------
pregunta = st.chat_input("Escribe tu pregunta, por ejemplo: ¿cuánto cuesta una limpieza dental?")

if st.session_state.pregunta_pendiente:
    pregunta = st.session_state.pregunta_pendiente
    st.session_state.pregunta_pendiente = None

if pregunta:
    st.session_state.historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user", avatar=AVATAR_USUARIO):
        st.markdown(pregunta)

    with st.chat_message("assistant", avatar=AVATAR_ASISTENTE):
        with st.spinner("Buscando en la documentación..."):
            respuesta, fuentes = responder_con_fuentes(cadena, retriever, pregunta)
        st.markdown(respuesta)
        mostrar_fuentes(fuentes)

    st.session_state.historial.append(
        {"rol": "assistant", "contenido": respuesta, "fuentes": fuentes}
    )
