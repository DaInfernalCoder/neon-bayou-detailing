#!/usr/bin/env python3
"""Scan public HTML prose against the shared trigger-word list."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path


BANNED_WORDS = {
    "get", "bank", "credit", "access", "open", "compare", "problem", "now", "billing", "deal",
    "finance", "financial", "claims", "claim", "insurance", "mortgage", "soon", "new",
    "performance", "freedom", "home", "sales", "medical", "urgent", "life", "marketing",
    "investment", "diagnostics", "friend", "cash", "invoice", "extra", "purchase", "vacation",
    "trial", "offshore", "luxury", "affordable", "debt", "bonus", "removal", "traffic", "gold",
    "cost", "costs", "sale", "legal", "order", "hard", "soft", "earnest", "modular",
    "manufactured", "income", "rebate", "warranty", "stop", "sample", "bulk", "container",
    "roll", "human", "fx", "rental", "success", "student", "fast", "equity", "product",
    "beverage", "solution", "medicine", "check", "profit", "profits", "form", "junk", "off",
    "obligation", "member", "buy", "guarantee", "loan", "loans", "all", "chance", "call",
    "million", "money", "foreclosure", "casino", "discount", "diagnostic", "phone", "medium",
    "timeshare", "supplies", "bankruptcy", "name", "rate", "rates", "terms", "cheap",
    "opportunity", "prize", "action", "act", "avoid", "offer", "price", "savings", "dollars",
    "billionaire", "amazing", "amazed", "click", "expire", "expires", "fantastic", "incredible",
    "instant", "jackpot", "limited", "lottery", "thousands", "unbelievable", "unlimited",
    "wonderful", "immediately", "certified", "accounts", "refund", "celebrity", "covid", "gift",
    "clearance", "card", "quote", "sex", "only", "vip", "free", "today", "score", "refinance",
    "billion", "winner", "winning", "selected", "congratulations", "cancel", "bargain",
    "promise", "spam", "subscribe", "subscription", "payment", "password", "deposit",
    "transaction", "transfer", "reward", "redeem", "coupon", "promo", "promotion", "hidden",
    "warning", "download", "verify", "breach", "weight", "pennies", "wholesale", "consolidate",
    "pre-approved", "retainer", "upfront", "charges", "earn", "earnings", "salary", "wage",
    "payout", "compensation", "commission", "yield", "returns", "interest", "principal",
    "collateral", "leverage", "capital", "fund", "funded", "funding", "raise", "raising",
    "raised", "pitch", "pitched", "close", "closed", "closing", "structured", "structure",
    "arrange", "arranged", "arrangement", "place", "placed", "placement", "originate",
    "originated", "origination", "underwrite", "underwritten", "underwriting", "syndicate",
    "syndicated", "syndication",
}
PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in sorted(BANNED_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


class PublicTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg"}:
            self.skip_depth += 1
        if not self.skip_depth:
            data = dict(attrs)
            for key in ("content", "alt", "aria-label", "title"):
                if data.get(key):
                    self.parts.append(data[key] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    args = parser.parse_args()

    source = args.html.read_text(encoding="utf-8")
    if args.html.suffix.lower() in {".html", ".htm"}:
        scan = PublicTextParser()
        scan.feed(source)
        prose = "\n".join(scan.parts)
    else:
        prose = source
    violations = sorted({match.group(1).lower() for match in PATTERN.finditer(prose)})
    print(f"public_text_characters={len(prose)}")
    print(f"violations={violations}")
    if violations:
        raise SystemExit(1)
    print("PASS public copy audit")


if __name__ == "__main__":
    main()
