"""
streamlit_app.py
------------------
Interfaz web del agente. Este es el archivo que Hugging Face Spaces ejecuta
para levantar la aplicación.
"""

import streamlit as st
from rag_chain import cargar_cadena_rag, responder_con_fuentes

st.set_page_config(page_title="Asistente Sonrisa Plena", page_icon="🦷")

st.title("🦷 Asistente virtual — Clínica Dental Sonrisa Plena")
st.caption(
    "Responde preguntas sobre citas, precios, coberturas y nuestra política de "
    "privacidad, con base en la documentación oficial de la clínica."
)


@st.cache_resource
def obtener_cadena():
    """Carga el índice y la cadena RAG una sola vez por sesión del servidor,
    no en cada pregunta (evita recargar el modelo de embeddings cada vez)."""
    return cargar_cadena_rag()


try:
    cadena, retriever = obtener_cadena()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

if "historial" not in st.session_state:
    st.session_state.historial = []

for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])
        if mensaje.get("fuentes"):
            st.caption(f"📎 Fuentes: {', '.join(mensaje['fuentes'])}")

pregunta = st.chat_input("Escribe tu pregunta, por ejemplo: ¿cuánto cuesta una limpieza dental?")

if pregunta:
    st.session_state.historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en la documentación..."):
            respuesta, fuentes = responder_con_fuentes(cadena, retriever, pregunta)
        st.markdown(respuesta)
        if fuentes:
            st.caption(f"📎 Fuentes: {', '.join(fuentes)}")

    st.session_state.historial.append(
        {"rol": "assistant", "contenido": respuesta, "fuentes": fuentes}
    )
