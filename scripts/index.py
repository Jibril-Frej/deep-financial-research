"""
Indexing script for SEC filings using LangChain and ChromaDB.
"""

import json

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from utils.config import settings
from utils.logging import logger

BATCH_SIZE = 100  # chunks per OpenAI embedding call


def load_document_metadata(raw_data_dir):
    """
    Load document metadata containing SEC filing URLs for each ticker.

    Returns:
        dict: A dictionary mapping ticker to document metadata
    """
    metadata_map = {}

    for metadata_file in raw_data_dir.glob("*_metadata.json"):
        try:
            ticker = metadata_file.stem.replace("_metadata", "")
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                metadata_map[ticker] = metadata
                logger.info("Loaded URL metadata for %s", ticker)
        except Exception as e:
            logger.debug("No metadata file for %s or failed to load: %s", metadata_file, e)

    return metadata_map


def run_indexing():
    """1. Loads raw text files from data/raw
    2. Splits them into chunks with metadata including URLs when available
    3. Indexes them into ChromaDB for retrieval
    """
    # 1. Initialize Embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)

    # 2. Load document metadata containing URLs (if available)
    metadata_map = load_document_metadata(settings.RAW_DATA_DIR)

    # 3. Prepare Splitter
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

        # Get document metadata with URLs if available
        doc_metadata = metadata_map.get(ticker, {})

        # Load and split
        loader = TextLoader(str(file_path))
        docs = loader.load()

        # Add comprehensive metadata to each chunk for links and filtered retrieval
        for doc in docs:
            doc.metadata = {
                "ticker": ticker,
                "section": section,
                "source": file_path.name,
                "file_path": str(file_path),  # Full file path for potential links
                "document_type": "SEC Filing",  # Could be expanded later
                "section_display": section.replace(
                    "_", " "
                ).title(),  # Human-readable section name
                # Add SEC document URL information if available
                "company_name": doc_metadata.get("company_name"),
                "filing_url": doc_metadata.get("filing_url"),
                "accession_number": doc_metadata.get("accession_number"),
                "period_of_report": doc_metadata.get("period_of_report"),
                "homepage_url": doc_metadata.get("homepage_url"),
            }

        chunks = text_splitter.split_documents(docs)
        all_documents.extend(chunks)
        logger.info(" ✅ Processed %s (%d chunks)", file_path.name, len(chunks))

    # 3. Create/Update Vector Store in batches with a progress bar
    total = len(all_documents)
    logger.info("📦 Indexing %d chunks into ChromaDB (batch size: %d)...", total, BATCH_SIZE)

    batches = [all_documents[i : i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    # Initialise the collection with the first batch, then add the rest
    vector_db = Chroma.from_documents(
        documents=batches[0],
        embedding=embeddings,
        persist_directory=str(settings.INDEX_DIR),
        collection_name="sec_filings",
    )
    for batch in tqdm(batches[1:], desc="Embedding batches", unit="batch"):
        vector_db.add_documents(batch)

    logger.info("🚀 Indexing complete! Your data is ready for LangGraph.")


if __name__ == "__main__":
    run_indexing()
