"""
loaders.py
-----------
Lee los documentos de la base de conocimiento (PDF, Markdown, HTML, CSV) y los
convierte en objetos `Document` de LangChain, cada uno con metadata que indica
de qué archivo salió. Esa metadata es la que después nos permite citar la
fuente en la respuesta del agente, en vez de responder "de la nada".

Cada tipo de archivo se trata distinto porque su estructura es distinta:
- Markdown / HTML: texto corrido, se puede fragmentar directamente.
- PDF: hay que extraer el texto de cada página primero.
- CSV: cada fila es un registro estructurado; conviene convertir cada fila en
  un "documento" propio (por ejemplo, cada servicio del tarifario), en vez de
  aplastar la tabla completa en un solo bloque de texto.
"""

from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pandas as pd
from langchain_core.documents import Document


def load_markdown(path: Path) -> list[Document]:
    """Lee un archivo .md y lo devuelve como un único Document."""
    texto = path.read_text(encoding="utf-8")
    return [Document(page_content=texto, metadata={"source": path.name, "tipo": "markdown"})]


def load_html(path: Path) -> list[Document]:
    """Lee un archivo .html, extrae solo el texto visible (sin tags) y lo
    devuelve como un único Document."""
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text(separator="\n", strip=True)
    return [Document(page_content=texto, metadata={"source": path.name, "tipo": "html"})]


def load_pdf(path: Path) -> list[Document]:
    """Lee un PDF y devuelve un Document por página, indicando el número de
    página en la metadata (útil para citar 'página 2' en vez de solo el
    nombre del archivo)."""
    reader = PdfReader(str(path))
    documentos = []
    for i, page in enumerate(reader.pages, start=1):
        texto = page.extract_text() or ""
        if texto.strip():
            documentos.append(
                Document(page_content=texto, metadata={"source": path.name, "tipo": "pdf", "pagina": i})
            )
    return documentos


def load_csv(path: Path) -> list[Document]:
    """Lee un CSV y convierte cada FILA en un Document independiente, con las
    columnas escritas como 'columna: valor'. Esto funciona mucho mejor para
    RAG que meter la tabla completa como un bloque de texto plano, porque
    cada fragmento recuperado corresponde a un solo servicio/registro
    concreto, no a la tabla entera."""
    df = pd.read_csv(path)
    documentos = []
    for idx, fila in df.iterrows():
        texto = "\n".join(f"{col}: {fila[col]}" for col in df.columns)
        documentos.append(
            Document(page_content=texto, metadata={"source": path.name, "tipo": "csv", "fila": int(idx)})
        )
    return documentos


LOADERS_POR_EXTENSION = {
    ".md": load_markdown,
    ".html": load_html,
    ".pdf": load_pdf,
    ".csv": load_csv,
}


def cargar_documentos(carpeta: str | Path) -> list[Document]:
    """Recorre la carpeta de documentos y aplica el loader correspondiente
    según la extensión de cada archivo. Devuelve la lista completa de
    Documents de todos los archivos combinados."""
    carpeta = Path(carpeta)
    todos_los_documentos: list[Document] = []

    for archivo in sorted(carpeta.iterdir()):
        extension = archivo.suffix.lower()
        loader = LOADERS_POR_EXTENSION.get(extension)
        if loader is None:
            print(f"⚠️  Extensión no soportada, se omite: {archivo.name}")
            continue
        docs = loader(archivo)
        print(f"✅ {archivo.name}: {len(docs)} documento(s) cargado(s)")
        todos_los_documentos.extend(docs)

    return todos_los_documentos


if __name__ == "__main__":
    # Prueba rápida: ejecutar `python loaders.py` desde la carpeta app/
    docs = cargar_documentos("../data/documentos")
    print(f"\nTotal de documentos cargados: {len(docs)}")
    print("\n--- Ejemplo del primer documento ---")
    print(docs[0].metadata)
    print(docs[0].page_content[:300])
