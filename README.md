# Agente de IA — Clínica Dental Sonrisa Plena

Agente conversacional (RAG) que responde preguntas de pacientes con base en
documentos internos de una clínica dental ficticia, construido como parte del
Challenge Alura Agentes.

> 📌 Este README se completará en la fase de documentación final con capturas
> y video del agente desplegado.

## ¿Qué hace?

Responde preguntas como:
- "¿Cuánto cuesta una limpieza dental?"
- "¿Cómo cancelo mi cita?"
- "¿Qué información recopilan sobre mí?"
- "¿Atienden los domingos?"

...usando únicamente el contenido de 4 documentos reales de la clínica, en
distintos formatos:

| Documento | Formato |
|---|---|
| FAQ de citas y agendamiento | Markdown |
| FAQ general de la clínica | HTML |
| Tarifario de servicios | CSV |
| Política de privacidad | PDF |

## Stack técnico

- **Lenguaje:** Python
- **Framework RAG:** LangChain
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (local, Hugging Face)
- **Vector store:** FAISS
- **LLM:** Google Gemini (`gemini-2.5-flash`)
- **Interfaz:** Streamlit
- **Despliegue:** Hugging Face Spaces

## Estructura del proyecto

```
agente-clinica-dental/
├── app/
│   ├── loaders.py         # Carga PDF, Markdown, HTML y CSV
│   ├── chunking.py        # Divide los documentos en fragmentos
│   ├── ingest.py           # Construye el índice FAISS (ejecutar una vez)
│   ├── rag_chain.py        # Recuperación + generación con Gemini
│   └── streamlit_app.py    # Interfaz web
├── data/
│   ├── documentos/         # Los 4 documentos fuente
│   └── faiss_index/        # Índice vectorial (se genera con ingest.py)
├── requirements.txt
├── .env.example
└── README.md
```

## Cómo correrlo localmente

1. Clona el repositorio e instala dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Coloca a `.env` tu API key de Google Gemini
   ([consíguela gratis aquí](https://aistudio.google.com/)).
3. Activa el entorno virtual:
   * En Windows
   ```
   .venv\Scripts\Activate.ps1
   ```
   * En Linux\Mac Os
   ```
   source .venv/bin/activate
   ```
4. Construye el índice vectorial (solo la primera vez, o si cambian los documentos):
   ```
   cd app
   python ingest.py
   ```
5. Levanta la interfaz:
   ```
   streamlit run streamlit_app.py
   ```

## Despliegue

Desplegado en **Hugging Face Spaces** (no requiere tarjeta de crédito para el
tier gratuito). Pasos de despliegue: *(se documentan en la Fase 5)*.

