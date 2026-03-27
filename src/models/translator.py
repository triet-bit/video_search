import asyncio
import logging
from deep_translator import GoogleTranslator

log = logging.getLogger(__name__)


def _sync_translate(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        log.error(f"Translation error: {e}")
        return text


async def translate_to_english(text: str) -> str:
    return await asyncio.to_thread(_sync_translate, text)


async def translate_many(texts: list[str]) -> list[str]:
    return await asyncio.gather(*[translate_to_english(t) for t in texts])