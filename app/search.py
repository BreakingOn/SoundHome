from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import re

def search_by_query(query: str, genres: Optional[List[str]] = None, limit: int = 5) -> List[Dict[str, str]]:
    
    search_query = build_search_query(query, genres)
    
    with DDGS() as ddgs:
        results = []
        for item in ddgs.text(search_query, max_results=limit*2):  
            if len(results) >= limit:
                break
                
            if is_valid_music_result(item, genres):
                results.append(format_result(item))
    
    return results

def build_search_query(query: str, genres: Optional[List[str]]) -> str:
    
    base = f'"{query}" (official OR music OR video OR audio)'
    
    if genres:
        genres_part = " OR ".join([f'"{genre}"' for genre in genres])
        base += f" ({genres_part})"
    
    
    base += " site:youtube.com OR site:open.spotify.com OR site:music.apple.com"
    
    return base

def is_valid_music_result(item: Dict[str, str], genres: Optional[List[str]]) -> bool:
    
    title = item["title"].lower()
    url = item["href"].lower()
    
    
    music_platforms = [
        "youtube.com", "spotify.com", "music.apple.com",
        "deezer.com", "yandex.ru/music", "soundcloud.com"
    ]
    
    if not any(platform in url for platform in music_platforms):
        return False
    
    
    if genres:
        title_genres = extract_genres_from_title(title)
        if not any(genre in title_genres for genre in genres):
            return False
    
    
    blacklist = ["lyrics", "karaoke", "cover", "tutorial", "remix"]
    if any(term in title for term in blacklist):
        return False
    
    return True

def extract_genres_from_title(title: str) -> List[str]:
    
    genre_keywords = {
        "pop": ["pop"],
        "rock": ["rock"],
        "hip-hop": ["hip hop", "hiphop", "rap"],
        "electronic": ["electronic", "edm", "dubstep"],
        
    }
    
    found_genres = []
    for genre, keywords in genre_keywords.items():
        if any(keyword in title for keyword in keywords):
            found_genres.append(genre)
    
    return found_genres

def format_result(item: Dict[str, str]) -> Dict[str, str]:
    """Форматирует результат поиска"""
    source = "YouTube" if "youtube.com" in item["href"] else "Spotify"
    
    return {
        "title": clean_title(item["title"], source),
        "url": item["href"],
        "source": source
    }

def clean_title(title: str, source: str) -> str:
    """Очищает заголовок от лишней информации"""
    
    title = re.sub(rf'\s*-\s*{source}.*$', '', title, flags=re.IGNORECASE)
    
    title = re.sub(r'\[.*?\]|\(.*?\)|\b(official|video|audio|mp3)\b', '', title, flags=re.IGNORECASE)
    return title.strip()