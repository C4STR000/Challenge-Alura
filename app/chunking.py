"""
chunking.py
------------
Divide los documentos ya cargados (ver loaders.py) en fragmentos ("chunks")
más pequeños. Esto es necesario porque:

1. Un documento completo puede ser demasiado largo para meterlo entero como
   contexto en el prompt del LLM.
2. Fragmentos más pequeños y específicos generan búsquedas por similitud más
   precisas: si alguien pregunta por el precio de una limpieza, queremos
   recuperar el fragmento que habla de limpieza, no todo el tarifario junto.

Usamos RecursiveCharacterTextSplitter de LangChain, que intenta cortar en
saltos de párrafo primero, luego en saltos de línea, luego en espacios —
en ese orden de preferencia — para no partir una oración a la mitad si se
puede evitar.

El "overlap" (solapamiento) hace que el final de un chunk se repita al
principio del siguiente, para no perder contexto si una idea queda justo en
el borde del corte.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def dividir_en_chunks(
    documentos: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[Document]:
    """Divide una lista de Documents en fragmentos más pequeños.

    chunk_size: tamaño objetivo de cada fragmento, en caracteres.
    chunk_overlap: cuántos caracteres se repiten entre un fragmento y el
    siguiente, para conservar contexto en los bordes del corte.

    Nota: los documentos que vienen del CSV (una fila = un documento, ver
    loaders.py) normalmente ya son cortos, así que el splitter los deja
    intactos sin partirlos — eso es justo el comportamiento que queremos.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documentos)
    return chunks


if __name__ == "__main__":
    # Prueba rápida: ejecutar `python chunking.py` desde la carpeta app/
    from loaders import cargar_documentos

    docs = cargar_documentos("../data/documentos")
    chunks = dividir_en_chunks(docs)

    print(f"Documentos originales: {len(docs)}")
    print(f"Chunks generados: {len(chunks)}")
    print("\n--- Ejemplo de un chunk ---")
    print(chunks[0].metadata)
    print(chunks[0].page_content)
