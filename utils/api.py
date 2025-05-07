"""
API utilities for interacting with the music service.
"""
import requests
import base64
import os
import threading
from urllib.parse import urlencode, quote
from config import _ENCODED_API, console

DOWNLOAD_DIR = "YourDownloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=0, i'
}

def get_base_url():
    """Decode and return the base API URL."""
    return base64.b64decode(_ENCODED_API).decode('utf-8')

def search_dab(query: str, search_type: str = "track", offset: int = 0):
    """
    Search for tracks or albums using the DAB API.
    
    Args:
        query: Search query string
        search_type: Type of search ("track" or "album")
        offset: Pagination offset
        
    Returns:
        JSON response or None if request failed
    """
    base_url = get_base_url()
    params = {"q": query, "offset": offset, "type": search_type}
    full_url = f"{base_url}/search?{urlencode(params)}"
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        console.print(f"[red]Request failed[/red]: {e}")
    return None

def fetch_all_results(query, search_type):
    """
    Fetch all pages of search results.
    
    Args:
        query: Search query string
        search_type: Type of search ("track" or "album")
        
    Returns:
        List of all items from all pages
    """
    all_items = []
    offset = 0
    while True:
        data = search_dab(query, search_type, offset=offset)
        if not data:
            break
        key = "tracks" if search_type == "track" else "albums"
        items = data.get(key, [])
        pagination = data.get("pagination", {})
        if not items:
            break
        all_items.extend(items)
        total = pagination.get("total", 0)
        limit = pagination.get("limit", len(items))
        offset += limit
        if offset >= total:
            break
    return all_items

def get_streaming_url(track_id):
    """
    Get the streaming URL for a track.
    
    Args:
        track_id: ID of the track
        
    Returns:
        Streaming URL or None if request failed
    """
    base_url = get_base_url()
    url = f"{base_url}/stream?trackId={track_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("url")
    except Exception as e:
        console.print(f"[red]Failed to get streaming URL[/red]: {e}")
    return None

def get_track_detail(track_id):
    """
    Get detailed information for a track.
    
    Args:
        track_id: ID of the track
        
    Returns:
        Track details as JSON or None if request failed
    """
    base_url = get_base_url()
    url = f"{base_url}/track/{track_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        console.print(f"[red]Failed to get track details[/red]: {e}")
    return None

def _download_worker(url: str, filename: str):
    """Worker function to download a file in the background."""
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=30) as r:
            r.raise_for_status()
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        console.print(f"[green]Download complete:[/green] {file_path}")
    except Exception as e:
        console.print(f"[red]Download failed[/red]: {e}")

def download_track(track_id: str) -> str:
    """Get the stream URL and download it in background."""
    stream_url = get_streaming_url(track_id)
    if not stream_url:
        return None

    filename = f"{track_id}.flac"

    thread = threading.Thread(target=_download_worker, args=(stream_url, filename), daemon=True)
    thread.start()

    return os.path.join(DOWNLOAD_DIR, filename)