"""
Indexing script for SEC filings using LangChain and ChromaDB.
"""

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.config import settings
from utils.logging import logger


def run_indexing():
    """1. Loads raw text files from data/raw
    2. Splits them into chunks with metadata
    3. Indexes them into ChromaDB for retrieval
    """
    # 1. Initialize Embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)

    # 2. Prepare Splitter
    # Chunk size 1000 is roughly 2-3 paragraphs; 100 overlap prevents context loss
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    all_documents = []
    raw_files = list(settings.RAW_DATA_DIR.glob("*.txt"))

    if not raw_files:
        logger.warning("No raw files found in data/raw. Run ingest_sec.py first!")
        return

    logger.info("📄 Found %d files. Starting processing...", len(raw_files))

    for file_path in raw_files:
        # Extract metadata from filename (e.g., NVDA_risks.txt)
        parts = file_path.stem.split("_")
        ticker = parts[0]
        section = parts[1] if len(parts) > 1 else "unknown"

        # Load and split
        loader = TextLoader(str(file_path))
        docs = loader.load()

        # Add metadata to each chunk for filtered retrieval later
        for doc in docs:
            doc.metadata = {"ticker": ticker, "section": section, "source": file_path.name}

        chunks = text_splitter.split_documents(docs)
        all_documents.extend(chunks)
        logger.info(" ✅ Processed %s (%d chunks)", file_path.name, len(chunks))

    # 3. Create/Update Vector Store
    logger.info("📦 Indexing %d chunks into ChromaDB...", len(all_documents))
    Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        persist_directory=str(settings.INDEX_DIR),
        collection_name="sec_filings",
    )

    logger.info("🚀 Indexing complete! Your data is ready for LangGraph.")


if __name__ == "__main__":
    run_indexing()
