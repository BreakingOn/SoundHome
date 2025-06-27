from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import re
import time
import random
import logging
from functools import wraps
from random import uniform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MUSIC_PLATFORMS = {
    "YouTube": r"youtube\.com|youtu\.be",
    "Spotify": r"spotify\.com",
    "Apple Music": r"music\.apple\.com",
    "Deezer": r"deezer\.com",
    "Yandex Music": r"music\.yandex\.(ru|com)",
    "SoundCloud": r"soundcloud\.com",
    "VK Music": r"vk\.com/music",
    "Bandcamp": r"bandcamp\.com",
    "Tidal": r"tidal\.com",
    "Amazon Music": r"amazon\.com/music"
}

def retry(max_retries=3, delay_range=(1.0, 3.0)):
    """Декоратор для повторных попыток с экспоненциальной задержкой"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        delay = random.uniform(*delay_range) * (attempt + 1)
                        logger.info(f"Retry #{attempt + 1} after {delay:.2f} seconds...")
                        time.sleep(delay)
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            raise last_exception if last_exception else Exception("Unknown error")
        return wrapper
    return decorator

def is_music_url(url: str) -> bool:
    """Проверяет, является ли URL музыкальной платформой"""
    return any(re.search(pattern, url) for pattern in MUSIC_PLATFORMS.values())

def clean_title(title: str, source: str) -> str:
    """Очищает заголовок от мусора"""
    title = re.sub(rf'\s*-\s*{source}.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'(official|lyrics?|video|audio|mp3|download|free|HD|HQ)', '', title, flags=re.IGNORECASE)
    return title.strip()

@retry(max_retries=3, delay_range=(2.0, 6.0))
def search_track(title: str, artist: str) -> Optional[List[Dict[str, str]]]:
    """Ищет трек с логированием времени и попыток"""
    query = f"{artist} - {title} (music OR official)"
    
    
    start_time = time.time()
    logger.info(f"▶️ Начало поиска: {query}")
    
    try:
        with DDGS() as ddgs:
            
            delay = random.uniform(2.0, 6.0)
            logger.info(f"⏳ Задержка перед запросом: {delay:.2f} сек")
            time.sleep(delay)
            
            
            search_start = time.time()
            raw_results = list(ddgs.text(query, max_results=20))
            search_duration = time.time() - search_start
            logger.info(f"🔍 Получено {len(raw_results)} результатов за {search_duration:.2f} сек")
            
            
            filtered_results = []
            seen_urls = set()
            
            for item in raw_results:
                url = item["href"]
                if url in seen_urls or not is_music_url(url):
                    continue
                
                source = next((name for name, pattern in MUSIC_PLATFORMS.items() 
                             if re.search(pattern, url)), "Other Music")
                
                filtered_results.append({
                    "title": clean_title(item["title"], source),
                    "url": normalize_music_url(url, source),
                    "source": source
                })
                
                if len(filtered_results) >= 5:
                    break
            
            total_time = time.time() - start_time
            logger.info(f"✅ Успешно. Найдено треков: {len(filtered_results)}. Общее время: {total_time:.2f} сек")
            return filtered_results if filtered_results else None
            
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {str(e)}")
        raise

def normalize_music_url(url: str, source: str) -> str:
    """Нормализует URL для музыкальных платформ"""
    if source == "VK Music":
        return re.sub(r'(vk\.com/)(audio|music/album)(-?\d+_\d+)', r'\1music/album/\3', url)
    elif source == "Yandex Music":
        return re.sub(r'(track/)\d+', r'\1', url)
    return url
