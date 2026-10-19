"""Employer-name normalisation for matching ATS companies to register entities.

Registers list legal entities ("Stripe Technology Company Limited",
"Stripe Payments UK Ltd"), so we strip legal suffixes and punctuation and
match on leading tokens.
"""

import re
import unicodedata

_SUFFIXES = {
    "limited", "ltd", "inc", "incorporated", "llc", "llp", "lp", "plc", "corp", "corporation",
    "co", "company", "gmbh", "mbh", "ag", "se", "sa", "sas", "sarl", "srl", "spa", "bv", "nv",
    "ab", "as", "asa", "aps", "oy", "oyj", "kk", "kabushiki", "kaisha", "pty", "pte", "ulc",
    "ug", "kg", "unlimited", "dac", "uc", "the", "holding", "holdings",
}


def normalize(name):
    """Lowercase, strip accents/punctuation and legal suffixes."""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = s.replace("&", " and ")
    s = re.split(r"\bt/a\b|\btrading as\b|\bdba\b|\bd/b/a\b", s)[0]
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"(?<=\b[a-z])\.(?=[a-z]\b)", "", s)  # b.v. -> bv
    s = re.sub(r"[^a-z0-9]+", " ", s)
    tokens = [t for t in s.split() if t not in _SUFFIXES]
    return " ".join(tokens)


# Words that commonly follow a brand in a subsidiary's legal name.
_GENERIC = {
    "uk", "gb", "ireland", "irish", "canada", "netherlands", "nederland", "holland", "denmark", "danmark",
    "europe", "european", "emea", "international", "global", "worldwide", "technology", "technologies",
    "tech", "software", "services", "solutions", "systems", "payments", "labs", "lab", "digital", "cloud",
    "operations", "development", "dev", "centre", "center", "research", "engineering", "networks",
    "security", "data", "online", "web", "ai", "germany", "deutschland", "japan", "singapore", "australia",
    "sweden", "finland", "switzerland", "group", "and", "of", "x",
}


def matches(alias_norm, entity_norm):
    """True if the register entity looks like the alias.

    Multi-word aliases match when the entity starts with them as whole
    words. A one-word alias ('stripe', 'okta') only matches when every
    following word is generic ('stripe payments uk', 'okta canada'), so
    'grab' does not match 'grab a bite catering'. Add exact register names
    to a company's aliases in companies.json for anything unusual."""
    if not alias_norm or not entity_norm:
        return False
    if alias_norm == entity_norm:
        return True
    if not entity_norm.startswith(alias_norm + " "):
        return False
    if " " in alias_norm:
        return True
    rest = entity_norm[len(alias_norm) + 1:].split()
    return all(w in _GENERIC for w in rest)
