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
- **LLM:** Google Gemini (`gemini-3.5-flash`)
- **Interfaz:** Streamlit
- **Despliegue:** Streamlit Community Cloud

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
2. Copia `.env.example` a `.env` y coloca tu API key de Google Gemini
   ([consíguela gratis aquí](https://aistudio.google.com/)).
3. Construye el índice vectorial (solo la primera vez, o si cambian los documentos):
   ```
   cd app
   python ingest.py
   ```
4. Levanta la interfaz:
   ```
   streamlit run streamlit_app.py
   ```

## Despliegue

Desplegado en **Streamlit Community Cloud** (la plataforma oficial de
Streamlit; no requiere tarjeta de crédito, solo una cuenta de GitHub).

1. Asegúrate de que tu repositorio esté subido a GitHub, **incluyendo el
   índice ya construido** (`data/faiss_index/index.faiss` y `index.pkl`),
   aunque normalmente estén en `.gitignore`:
   ```
   git add -f data/faiss_index/index.faiss data/faiss_index/index.pkl
   git add .
   git commit -m "Preparar despliegue"
   git push
   ```
2. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con
   tu cuenta de GitHub (sin tarjeta).
3. Clic en **"Create app"** → elige tu repositorio, la rama (`main`) y como
   *Main file path* escribe: `app/streamlit_app.py`
4. Antes de desplegar, en **"Advanced settings" → Secrets**, agrega:
   ```
   GOOGLE_API_KEY = "tu_api_key_aqui"
   ```
5. Clic en **Deploy**. La primera vez tarda unos minutos mientras instala
   `requirements.txt` y descarga el modelo de embeddings.

> Nota técnica: el índice vectorial (`data/faiss_index/`) va incluido en el
> repositorio para que la app no tenga que reconstruirlo al iniciar. Si
> agregas documentos nuevos, usa la función "Agregar documentación" dentro de
> la propia interfaz — reconstruye el índice automáticamente.
