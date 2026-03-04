"""Fetches the latest 10-K filings for all S&P 500 companies from EDGAR."""

import json
import logging
import os
import time
from io import StringIO

import pandas as pd
import requests
from edgar import Company, set_identity
from edgar.company_reports import TenK
from edgar.entity.core import CompanyNotFoundError

from utils.config import settings
from utils.logging import logger

# Suppress edgartools' verbose internal logging (legacy parser fallbacks, etc.)
logging.getLogger("edgar").setLevel(logging.ERROR)

# Set the identity for EDGAR API access
set_identity(settings.EDGAR_IDENTITY.get_secret_value())


def get_sp500_companies() -> list[dict]:
    """Fetches the current S&P 500 companies from Wikipedia.

    Returns a list of dicts with ticker, company_name, and gics_sector.
    """
    logger.info("Fetching S&P 500 companies from Wikipedia...")
    response = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    response.raise_for_status()
    df = pd.read_html(StringIO(response.text))[0]
    result = [
        {
            "ticker": row["Symbol"].replace(".", "-"),
            "company_name": row["Security"],
            "gics_sector": row["GICS Sector"],
        }
        for _, row in df.iterrows()
    ]
    logger.info("Found %d S&P 500 companies.", len(result))
    return result


def _safe_get_section(tenk: TenK, attr: str, ticker: str, section_name: str) -> str | None:
    """Returns a TenK section's text, or None if parsing fails."""
    try:
        return getattr(tenk, attr)
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning("  ⚠️  Could not parse %s for %s: %s", section_name, ticker, e)
        return None


def download_financial_sections(
    ticker: str,
    company_name: str,
    gics_sector: str,
    folder=settings.RAW_DATA_DIR,
) -> None:
    """
    Downloads key sections of the latest 10-K for a ticker.
    Saves them as separate .txt files for granular RAG.
    Also saves document metadata including the original SEC filing URL.
    Skips the ticker if already downloaded.
    """
    os.makedirs(folder, exist_ok=True)

    # Skip if already downloaded (allows resuming interrupted runs)
    metadata_path = folder / f"{ticker}_metadata.json"
    if metadata_path.exists():
        logger.info("⏭️  Skipping %s (already downloaded).", ticker)
        return

    logger.info("🔍 Fetching 10-K for %s from EDGAR...", ticker)

    edgar_company = Company(ticker)
    filings = edgar_company.get_filings(form="10-K")

    if not filings:
        logger.warning("❌ No 10-K found for %s", ticker)
        return

    latest_filing = filings.latest()
    tenk: TenK = latest_filing.obj()

    document_metadata = {
        "ticker": ticker,
        "company_name": company_name,
        "gics_sector": gics_sector,
        "filing_url": latest_filing.filing_url,
        "accession_number": latest_filing.accession_number,
        "period_of_report": str(latest_filing.period_of_report),
        "homepage_url": getattr(latest_filing, "homepage_url", latest_filing.filing_url),
    }

    sections = {
        "business": _safe_get_section(tenk, "business", ticker, "business"),
        "risks": _safe_get_section(tenk, "risk_factors", ticker, "risks"),
        "mnda": _safe_get_section(tenk, "management_discussion", ticker, "mnda"),
    }

    for section_name, content in sections.items():
        if content:
            file_path = folder / f"{ticker}_{section_name}.txt"
            file_path.write_text(content, encoding="utf-8")
            logger.info("  ✅ Saved %s_%s.txt", ticker, section_name)
        else:
            logger.warning("  ⚠️  Could not find %s for %s", section_name, ticker)

    metadata_path.write_text(json.dumps(document_metadata, indent=2), encoding="utf-8")
    logger.info("  ✅ Saved %s metadata.", ticker)


if __name__ == "__main__":
    sp500 = get_sp500_companies()

    failed: list[str] = []
    for i, entry in enumerate(sp500, start=1):
        t = entry["ticker"]
        logger.info("--- [%d/%d] %s ---", i, len(sp500), t)
        try:
            download_financial_sections(
                ticker=t,
                company_name=entry["company_name"],
                gics_sector=entry["gics_sector"],
            )
        except (OSError, RuntimeError, KeyError, ValueError, CompanyNotFoundError) as e:
            logger.error("❌ Failed for %s: %s", t, e)
            failed.append(t)

        # Respect EDGAR's rate limits (10 req/sec max, be conservative)
        time.sleep(0.5)

    logger.info("✅ Done. %d/%d tickers succeeded.", len(sp500) - len(failed), len(sp500))
    if failed:
        logger.warning("Failed tickers: %s", failed)
