# application/core/i18n.py

import json
from pathlib import Path
from typing import Dict, Optional
import redis.asyncio as redis
from application.core.config import settings
from application.core.log import logger

# In-memory translation cache
_translations: Dict[str, Dict[str, str]] = {}

# Reverse lookup cache for slug detection
_reverse_lookup: Dict[str, Dict[str, str]] = {}


async def init_translations(redis_client: redis.Redis) -> None:
    """
    Initialize translations from JSON files to cache and Redis

    Args:
        redis_client: Redis client instance
    """
    global _translations, _reverse_lookup

    try:
        locales_path = Path(settings.LOCALES_PATH)

        if not locales_path.exists():
            logger.warning(f"⚠️ Locales path not found: {locales_path}")
            return

        # Get all JSON files
        json_files = list(locales_path.glob("*.json"))

        if not json_files:
            logger.warning(f"⚠️ No translation files found in {locales_path}")
            return

        # Use pipeline for batch Redis operations
        pipe = redis_client.pipeline()

        for file in json_files:
            lang = file.stem

            # Skip unsupported languages
            if lang not in settings.SUPPORTED_LANGS:
                logger.debug(f"Skipping unsupported language: {lang}")
                continue

            try:
                # Load translations from file
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not data:
                    logger.warning(f"⚠️ Empty translation file: {file}")
                    continue

                # Flatten nested dict for Redis
                flat_data = _flatten_dict(data)

                # Store in memory cache (primary)
                _translations[lang] = flat_data

                # Build reverse lookup for this language
                _reverse_lookup[lang] = {v: k for k, v in flat_data.items()}

                # Store in Redis (backup/sync)
                redis_key = f"i18n:{lang}"
                pipe.delete(redis_key)
                pipe.hset(redis_key, mapping=flat_data)

                logger.info(f"📦 Loaded {len(flat_data)} translations for '{lang}'")

            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {file}: {e}")
            except Exception as e:
                logger.error(f"❌ Error loading {file}: {e}")

        # Execute all Redis operations
        await pipe.execute()

        logger.info(f"✅ Initialized {len(_translations)} languages: {list(_translations.keys())}")

    except Exception as e:
        logger.error(f"❌ Critical error initializing translations: {e}")
        raise


def detect_slug(text: str, lang: Optional[str] = None, threshold: float = 0.8) -> Optional[str]:
    """
    Detect translation slug from text using fuzzy matching

    Args:
        text: Input text to find slug for
        lang: Specific language to search in (None for all languages)
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        Translation slug if found, None otherwise

    Example:
        detect_slug("Welcome", "en") -> "welcome.message"
        detect_slug("Добро пожаловать") -> "welcome.message"
    """
    if not text or not text.strip():
        return None

    text = text.strip()
    text_lower = text.lower()

    # Exact match (case insensitive)
    if lang:
        # Search in specific language
        if lang in _reverse_lookup:
            for translation, slug in _reverse_lookup[lang].items():
                if translation.lower() == text_lower:
                    return slug
    else:
        # Search in all languages
        for lang_code, reverse_dict in _reverse_lookup.items():
            for translation, slug in reverse_dict.items():
                if translation.lower() == text_lower:
                    return slug

    # Fuzzy match for similar texts
    best_match = None
    best_similarity = 0.0

    search_dicts = _reverse_lookup.items() if not lang else [(lang, _reverse_lookup.get(lang, {}))]

    for lang_code, reverse_dict in search_dicts:
        for translation, slug in reverse_dict.items():
            similarity = _calculate_similarity(text, translation)
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = slug

    if best_match:
        logger.debug(f"🔍 Found slug '{best_match}' for text '{text}' (similarity: {best_similarity:.2f})")
        return best_match

    return None


def detect_slug_multilingual(text: str, preferred_langs: list[str] = None) -> Dict[str, Optional[str]]:
    """
    Detect slug across multiple languages and return results for each language

    Args:
        text: Input text to find slug for
        preferred_langs: List of languages to check (None for all available)

    Returns:
        Dict with language codes as keys and slugs as values

    Example:
        detect_slug_multilingual("Welcome", ["en", "ru"])
        -> {'en': 'welcome.message', 'ru': 'welcome.message', 'uz': None}
    """
    result = {}

    langs_to_check = preferred_langs if preferred_langs else get_available_languages()

    for lang in langs_to_check:
        result[lang] = detect_slug(text, lang)

    return result


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts (0.0 to 1.0)

    Uses a combination of methods for better accuracy
    """
    if not text1 or not text2:
        return 0.0

    text1 = text1.lower().strip()
    text2 = text2.lower().strip()

    # Exact match
    if text1 == text2:
        return 1.0

    # Contains match
    if text1 in text2 or text2 in text1:
        return 0.9

    # Word-based similarity
    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    jaccard_similarity = len(intersection) / len(union) if union else 0.0

    return jaccard_similarity


def slug_to_text(slug: str, lang: str = "en", **kwargs) -> str:
    """
    Alias for t() function - get text from slug

    Args:
        slug: Translation slug
        lang: Language code
        **kwargs: Format parameters

    Returns:
        Translated text
    """
    return t(slug, lang, **kwargs)


def text_to_slug(text: str, lang: Optional[str] = None) -> Optional[str]:
    """
    Alias for detect_slug() - get slug from text

    Args:
        text: Input text
        lang: Language code (None for all languages)

    Returns:
        Translation slug or None
    """
    return detect_slug(text, lang)


def get_slugs_by_pattern(pattern: str, lang: str = "en") -> Dict[str, str]:
    """
    Get all slugs and texts matching a pattern

    Args:
        pattern: Pattern to search for in slugs
        lang: Language code

    Returns:
        Dict of matching slugs and their texts
    """
    if lang not in _translations:
        return {}

    result = {}
    for slug, text in _translations[lang].items():
        if pattern in slug:
            result[slug] = text

    return result


# Existing functions remain the same...
def _flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, str(v)))
    return dict(items)


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translation for key"""
    if lang in _translations:
        value = _translations[lang].get(key)
        if value is not None:
            return _format_string(value, key, lang, **kwargs)

    if lang != settings.DEFAULT_LANGUAGE:
        if settings.DEFAULT_LANGUAGE in _translations:
            value = _translations[settings.DEFAULT_LANGUAGE].get(key)
            if value is not None:
                logger.debug(f"Using fallback language for key: {key}")
                return _format_string(value, key, settings.DEFAULT_LANGUAGE, **kwargs)

    logger.warning(f"⚠️ Translation not found: key='{key}', lang='{lang}'")
    return key


def _format_string(value: str, key: str, lang: str, **kwargs) -> str:
    """Format string with parameters safely"""
    if not kwargs:
        return value

    try:
        return value.format(**kwargs)
    except KeyError as e:
        logger.warning(f"⚠️ Missing format parameter {e} for key '{key}' in '{lang}'")
        return value
    except Exception as e:
        logger.error(f"❌ Format error for key '{key}' in '{lang}': {e}")
        return value


def get_available_languages() -> list[str]:
    """Get list of available language codes"""
    return list(_translations.keys())


def is_language_available(lang: str) -> bool:
    """Check if language is available"""
    return lang in _translations