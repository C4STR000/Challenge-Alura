"""
rag_chain.py
-------------
El corazón del agente. Dado el índice FAISS ya construido (ver ingest.py),
esta pieza:

1. Recibe la pregunta del usuario.
2. Recupera los K fragmentos más relevantes del índice (retrieval).
3. Arma un prompt que incluye esos fragmentos como contexto.
4. Llama a Gemini para redactar la respuesta final, con instrucciones
   estrictas de responder SOLO con base en el contexto — y de decir
   explícitamente que no tiene esa información si el contexto no la cubre,
   en vez de inventar una respuesta (alucinar).

Este último punto es clave para la Política de Privacidad: es el documento
que "no puede fallar", así que preferimos un "no tengo esa información" a
una respuesta inventada con apariencia de verdad.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
os.environ["HF_HUB_OFFLINE"] = "1"

CARPETA_INDICE = Path(__file__).parent.parent / "data" / "faiss_index"
MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"
MODELO_LLM = "gemini-3.5-flash"
K_FRAGMENTOS = 4  # cuántos fragmentos recuperar por pregunta

PROMPT_SISTEMA = """Eres el asistente virtual de Clínica Dental Sonrisa Plena.
Respondes preguntas de pacientes usando ÚNICAMENTE la información del
contexto proporcionado abajo. No inventes datos, precios, horarios ni
políticas que no aparezcan explícitamente en el contexto.

Si la pregunta no se puede responder con el contexto disponible, dilo con
claridad: "No tengo esa información en mi base de conocimiento actual, te
recomiendo contactar directamente a la clínica al 55 1234 5678." No intentes
adivinar ni completar con conocimiento general.

Responde en español, de forma clara, amable y concisa.

Contexto:
{contexto}

Pregunta del paciente:
{pregunta}

Respuesta:"""


def cargar_cadena_rag():
    """Carga el índice FAISS ya construido y arma la cadena de recuperación
    + generación. Se llama una sola vez al iniciar la app (ver
    streamlit_app.py), no en cada pregunta."""

    if not CARPETA_INDICE.exists():
        raise FileNotFoundError(
            f"No se encontró el índice en {CARPETA_INDICE}. "
            "Ejecuta primero: python ingest.py"
        )

    embeddings = HuggingFaceEmbeddings(model_name=MODELO_EMBEDDINGS)
    indice = FAISS.load_local(
        str(CARPETA_INDICE), embeddings, allow_dangerous_deserialization=True
    )
    retriever = indice.as_retriever(search_kwargs={"k": K_FRAGMENTOS})

    llm = ChatGoogleGenerativeAI(
        model=MODELO_LLM,
        google_api_key=os.environ["GOOGLE_API_KEY"],
        temperature=0.2,  # baja temperatura: respuestas más apegadas al contexto, menos "creativas"
    )

    prompt = ChatPromptTemplate.from_template(PROMPT_SISTEMA)

    def formatear_contexto(chunks_recuperados):
        """Junta los fragmentos recuperados en un solo bloque de texto,
        indicando de qué documento salió cada uno."""
        bloques = []
        for doc in chunks_recuperados:
            fuente = doc.metadata.get("source", "desconocido")
            bloques.append(f"[Fuente: {fuente}]\n{doc.page_content}")
        return "\n\n---\n\n".join(bloques)

    cadena = (
        {
            "contexto": retriever | formatear_contexto,
            "pregunta": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return cadena, retriever


def responder_con_fuentes(cadena, retriever, pregunta: str):
    """Devuelve la respuesta del agente junto con la lista de documentos
    fuente usados, para poder mostrarlos en la interfaz (transparencia:
    el paciente puede ver de dónde salió la información)."""
    respuesta = cadena.invoke(pregunta)
    fragmentos = retriever.invoke(pregunta)
    fuentes = sorted({doc.metadata.get("source", "desconocido") for doc in fragmentos})
    return respuesta, fuentes


if __name__ == "__main__":
    # Prueba rápida por consola: ejecutar `python rag_chain.py` desde app/
    # (requiere GOOGLE_API_KEY configurada como variable de entorno)
    cadena, retriever = cargar_cadena_rag()

    print("Agente de Clínica Dental Sonrisa Plena — escribe 'salir' para terminar\n")
    while True:
        pregunta = input("Paciente: ")
        if pregunta.lower() in {"salir", "exit"}:
            break
        respuesta, fuentes = responder_con_fuentes(cadena, retriever, pregunta)
        print(f"\nAgente: {respuesta}")
        print(f"(Fuentes: {', '.join(fuentes)})\n")
