"""
API utilities for interacting with the music service.
"""
import requests
import base64
from urllib.parse import urlencode, quote
from config import _ENCODED_API, console

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