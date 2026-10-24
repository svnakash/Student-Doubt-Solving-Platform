import re


BAD_WORDS = {
    "damn",
    "hell",
    "shit",
    "crap",
    "idiot",
    "stupid",
    "moron",
    "loser",
    "fool",
    "bitch",
    "asshole",
    "dumb",
    "hate",
    "screw you",
    "fuck",
    "f u c k",
}


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def contains_inappropriate_language(text: str) -> bool:
    """Return True when the text contains offensive or abusive language."""
    if not isinstance(text, str):
        return False

    normalized = _normalize_for_match(text)
    if not normalized:
        return False

    for word in BAD_WORDS:
        normalized_word = _normalize_for_match(word)
        if not normalized_word:
            continue
        if normalized_word in normalized:
            return True

    return False
