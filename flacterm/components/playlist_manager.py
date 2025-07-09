import json
import os
from typing import Dict, List, Optional

class PlaylistManager:
    def __init__(self, playlists_file="playlists.json"):
        self.playlists_file = playlists_file
        self.playlists: Dict[str, List[dict]] = {}
        self.load_playlists()
    
    def load_playlists(self):
        """Load playlists from JSON file."""
        try:
            if os.path.exists(self.playlists_file):
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
        except Exception as e:
            print(f"Error loading playlists: {e}")
            self.playlists = {}
    
    def save_playlists(self):
        """Save playlists to JSON file."""
        try:
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving playlists: {e}")
            return False
    
    def create_playlist(self, name: str) -> bool:
        """Create a new empty playlist."""
        if not name or name in self.playlists:
            return False
        
        self.playlists[name] = []
        return self.save_playlists()
    
    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist."""
        if name not in self.playlists:
            return False
        
        del self.playlists[name]
        return self.save_playlists()
    
    def get_playlist_names(self) -> List[str]:
        """Get list of all playlist names."""
        return list(self.playlists.keys())
    
    def get_playlist(self, name: str) -> List[dict]:
        """Get tracks from a specific playlist."""
        return self.playlists.get(name, [])
    
    def add_track_to_playlist(self, playlist_name: str, track: dict) -> bool:
        """Add a track to a playlist."""
        if playlist_name not in self.playlists:
            return False
        
        # Check if track already exists in playlist (by ID)
        track_id = track.get("id")
        if track_id:
            for existing_track in self.playlists[playlist_name]:
                if existing_track.get("id") == track_id:
                    return False  # Track already exists
        
        self.playlists[playlist_name].append(track)
        return self.save_playlists()
    
    def remove_track_from_playlist(self, playlist_name: str, track_index: int) -> bool:
        """Remove a track from a playlist by index."""
        if playlist_name not in self.playlists:
            return False
        
        playlist = self.playlists[playlist_name]
        if 0 <= track_index < len(playlist):
            playlist.pop(track_index)
            return self.save_playlists()
        
        return False
    
    def remove_track_by_id(self, playlist_name: str, track_id: str) -> bool:
        """Remove a track from a playlist by track ID."""
        if playlist_name not in self.playlists:
            return False
        
        playlist = self.playlists[playlist_name]
        for i, track in enumerate(playlist):
            if track.get("id") == track_id:
                playlist.pop(i)
                return self.save_playlists()
        
        return False
    
    def get_playlist_count(self, name: str) -> int:
        """Get number of tracks in a playlist."""
        return len(self.playlists.get(name, []))
    
    def rename_playlist(self, old_name: str, new_name: str) -> bool:
        """Rename a playlist."""
        if old_name not in self.playlists or new_name in self.playlists or not new_name:
            return False
        
        self.playlists[new_name] = self.playlists.pop(old_name)
        return self.save_playlists()
    
    def clear_playlist(self, name: str) -> bool:
        """Clear all tracks from a playlist."""
        if name not in self.playlists:
            return False
        
        self.playlists[name] = []
        return self.save_playlists()