"""
Generate brand alias mappings for S&P 500 companies.

Reads sp500_companies.json (written by index.py), asks an LLM to produce
common brand/trade names for each company, and writes sp500_aliases.json:

    { "google": "GOOGL", "youtube": "GOOGL", "facebook": "META", ... }

Run once after indexing:
    python scripts/generate_sp500_aliases.py
"""

import json
import sys

from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm

from utils.config import settings
from utils.logging import logger


class _CompanyAliases(BaseModel):
    """Structured output for a single company's brand aliases."""

    aliases: list[str]
    """Common brand/product/trade names that unambiguously refer to this company (lowercase)."""


def _build_prompt(ticker: str, company_name: str) -> str:
    return f"""You are a business knowledge expert.

List the common brand names, product names, or informal names that people use when referring to this company.

Company: {ticker} — {company_name}

Rules:
- Only include names that clearly and unambiguously refer to THIS specific company.
- Do NOT include generic words, sector names, or names shared with other companies.
- Include the official short name if it differs from the legal name (e.g. "apple" for "Apple Inc.").
- All aliases must be lowercase.
- If the company has no well-known aliases beyond its legal name, return an empty list."""


def generate_aliases(companies: dict[str, dict]) -> dict[str, str]:
    """Call the LLM once per company and merge alias dictionaries.

    Args:
        companies: Mapping of ticker -> {company_name, ...} from sp500_companies.json.

    Returns:
        Merged alias -> ticker mapping (all keys lowercased).
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
    items = [
        (ticker, info["company_name"])
        for ticker, info in companies.items()
        if info.get("company_name")
    ]
    aliases: dict[str, str] = {}

    for ticker, company_name in tqdm(items, desc="Generating aliases", unit="company"):

        response = client.beta.chat.completions.parse(
            model="gpt-4.1",
            messages=[{"role": "user", "content": _build_prompt(ticker, company_name)}],
            response_format=_CompanyAliases,
            temperature=0,
        )

        result = response.choices[0].message.parsed
        if result is None:
            logger.warning("No parsed result for %s — skipping", ticker)
            continue

        for alias in result.aliases:
            clean = alias.lower().strip()
            if clean:
                aliases[clean] = ticker

    return aliases


def main():
    """Load companies, generate aliases, and write sp500_aliases.json."""
    lookup_path = settings.INDEX_DIR / "sp500_companies.json"
    if not lookup_path.exists():
        logger.error("sp500_companies.json not found at %s — run index.py first", lookup_path)
        sys.exit(1)

    with open(lookup_path, "r", encoding="utf-8") as f:
        companies: dict[str, dict] = json.load(f)

    logger.info("Generating aliases for %d companies", len(companies))
    aliases = generate_aliases(companies)
    logger.info("Generated %d aliases total", len(aliases))

    output_path = settings.INDEX_DIR / "sp500_aliases.json"
    output_path.write_text(json.dumps(aliases, indent=2, sort_keys=True), encoding="utf-8")
    logger.info("Aliases written to %s", output_path)


if __name__ == "__main__":
    main()
