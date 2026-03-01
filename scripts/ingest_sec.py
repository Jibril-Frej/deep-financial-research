"""Uses the `edgar` library to fetch the latest 10-K filings for specified companies."""

import json
import os

from edgar import Company, set_identity
from edgar.company_reports import TenK

from utils.config import settings
from utils.logging import logger

# Set the identity for EDGAR API access
set_identity(settings.EDGAR_IDENTITY.get_secret_value())


def download_financial_sections(ticker, folder=settings.RAW_DATA_DIR):
    """
    Downloads key sections of the latest 10-K for a ticker.
    Saves them as separate .txt files for granular RAG.
    Also saves document metadata including the original SEC filing URL.
    """
    os.makedirs(folder, exist_ok=True)

    logger.info("🔍 Fetching 10-K for %s from EDGAR...", ticker)

    company = Company(ticker)
    filings = company.get_filings(form="10-K")

    if not filings:
        logger.warning("❌ No 10-K found for %s", ticker)
        return

    latest_filing = filings.latest()
    tenk: TenK = latest_filing.obj()

    # Capture document metadata for URL linking
    document_metadata = {
        "ticker": ticker,
        "filing_url": latest_filing.filing_url,
        "accession_number": latest_filing.accession_number,
        "period_of_report": str(latest_filing.period_of_report),
        "homepage_url": getattr(latest_filing, "homepage_url", latest_filing.filing_url),
    }

    # Define the sections we want to extract
    sections = {
        "business": tenk.business,
        "risks": tenk.risk_factors,
        "mnda": tenk.management_discussion,
    }

    for section_name, content in sections.items():
        if content:
            # Create a clean filename: e.g., NVDA_risks.txt
            filename = f"{ticker}_{section_name}.txt"
            file_path = folder / filename

            # Use Pathlib's easy write method
            file_path.write_text(content, encoding="utf-8")
            logger.info(" ✅ Saved %s", filename)
        else:
            logger.warning(" ⚠️  Could not find %s for %s", section_name, ticker)

    # Save metadata for URL linking
    metadata_filename = f"{ticker}_metadata.json"
    metadata_path = folder / metadata_filename
    metadata_path.write_text(json.dumps(document_metadata, indent=2), encoding="utf-8")
    logger.info(" ✅ Saved document metadata: %s", metadata_filename)

    return document_metadata


if __name__ == "__main__":
    # Test with a few tech giants
    for t in ["NVDA", "AAPL"]:
        download_financial_sections(t)
