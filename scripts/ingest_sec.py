"""Uses the `edgar` library to fetch the latest 10-K filings for specified companies."""

import os

from edgar import Company, set_identity
from edgar.company_reports import TenK

from utils.config import settings
from utils.logging import logger

# Set the identity for EDGAR API access
set_identity(settings.EDGAR_IDENTITY)


def download_financial_sections(ticker, folder=settings.RAW_DATA_DIR):
    """
    Downloads key sections of the latest 10-K for a ticker.
    Saves them as separate .txt files for granular RAG.
    """
    os.makedirs(folder, exist_ok=True)

    logger.info(f"🔍 Fetching 10-K for {ticker} from EDGAR...")

    company = Company(ticker)
    filings = company.get_filings(form="10-K")

    if not filings:
        print(f"❌ No 10-K found for {ticker}")
        return

    latest_filing = filings.latest()
    tenk: TenK = latest_filing.obj()

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
            logger.info(f" ✅ Saved {filename}")
        else:
            logger.warning(f" ⚠️  Could not find {section_name} for {ticker}")


if __name__ == "__main__":
    # Test with a few tech giants
    for t in ["NVDA", "AAPL"]:
        download_financial_sections(t)
