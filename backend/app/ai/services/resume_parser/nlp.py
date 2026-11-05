"""
Natural Language Processing singleton helper for spaCy.
Implements lazy-loading of en_core_web_sm with lightweight pipeline configuration
and deterministic fallback when spaCy is unavailable.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_SPACY_NLP = None
_SPACY_LOAD_ATTEMPTED = False


def get_spacy_nlp():
    """
    Retrieve the singleton spaCy Language instance.
    Loads en_core_web_sm lazily on first access.
    Returns None if the model cannot be loaded, enabling deterministic fallback.
    """
    global _SPACY_NLP, _SPACY_LOAD_ATTEMPTED

    if _SPACY_NLP is not None:
        return _SPACY_NLP

    if _SPACY_LOAD_ATTEMPTED:
        return None

    _SPACY_LOAD_ATTEMPTED = True

    try:
        import spacy
        # Load lightweight pipeline: disable parser and lemmatizer to save RAM and CPU
        nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        _SPACY_NLP = nlp
        logger.info("Successfully loaded spaCy 'en_core_web_sm' model.")
        return _SPACY_NLP
    except Exception as exc:
        logger.warning(
            "Could not load spaCy model 'en_core_web_sm' (%s). "
            "Falling back to deterministic heuristic extraction.",
            exc,
        )
        _SPACY_NLP = None
        return None

