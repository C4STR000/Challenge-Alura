"""
ingest.py
----------
Este script se ejecuta UNA VEZ (o cada vez que cambian los documentos) para
construir la base vectorial. No se ejecuta en cada pregunta del usuario —
eso sería lentísimo. En su lugar:

1. Carga los documentos (loaders.py)
2. Los divide en chunks (chunking.py)
3. Convierte cada chunk en un embedding (vector numérico) usando un modelo
   local de Hugging Face, sin costo y sin depender de una API externa
4. Guarda el índice FAISS resultante en disco, en data/faiss_index/

Después, rag_chain.py simplemente CARGA ese índice ya construido — no lo
vuelve a calcular en cada consulta.

Ejecutar con:
    python ingest.py
desde la carpeta app/.
"""

from pathlib import Path
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from loaders import cargar_documentos
from chunking import dividir_en_chunks

os.environ["HF_HUB_OFFLINE"] = "1"  # el modelo ya está en caché local tras la primera descarga

CARPETA_DOCUMENTOS = Path(__file__).parent.parent / "data" / "documentos"
CARPETA_INDICE = Path(__file__).parent.parent / "data" / "faiss_index"

# Modelo de embeddings local. "MiniLM" es pequeño y rápido — suficiente para
# un corpus chico como el nuestro (4 documentos), y no requiere API key.
MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"


def construir_indice():
    print("1/4 — Cargando documentos...")
    documentos = cargar_documentos(CARPETA_DOCUMENTOS)

    print("\n2/4 — Dividiendo en chunks...")
    chunks = dividir_en_chunks(documentos)
    print(f"   {len(chunks)} chunks generados a partir de {len(documentos)} documentos")

    print("\n3/4 — Calculando embeddings (puede tardar un poco la primera vez)...")
    embeddings = HuggingFaceEmbeddings(model_name=MODELO_EMBEDDINGS)
    indice = FAISS.from_documents(chunks, embeddings)

    print("\n4/4 — Guardando índice en disco...")
    CARPETA_INDICE.mkdir(parents=True, exist_ok=True)
    indice.save_local(str(CARPETA_INDICE))

    print(f"\n✅ Índice guardado en {CARPETA_INDICE}")


if __name__ == "__main__":
    construir_indice()
