from shazamio import Shazam
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
shazam = Shazam()

async def recognize_song(file_path: str) -> Optional[Dict[str, Any]]:
    """Распознаёт трек через Shazam и возвращает метаданные"""
    try:
        data = await shazam.recognize(file_path)
        if not data or "track" not in data:
            logger.warning("No track found in Shazam response")
            return None
        
        track = data["track"]
        return {
            "title": track.get("title", "Unknown Title"),
            "artist": track.get("subtitle", "Unknown Artist"),
            "genres": track.get("genres", {}).get("primary", ""),
            "shazam_url": track.get("url", ""),
        }
    except Exception as e:
        logger.error(f"Shazam recognition error: {e}")
        return None