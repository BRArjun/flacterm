"""
Playlist manager component for DAB Terminal Music Player.
Handles playlist creation, saving, loading, and modification.
"""
import os
import json
from typing import List, Dict, Optional, Callable
from rich.console import Console

console = Console()

class PlaylistManager:
    """
    Manages playlists for the music player.
    Stores playlists in JSON files under the 'playlists' directory.
    """
    
    def __init__(self, playlist_dir="playlists"):
        """
        Initialize the playlist manager.
        
        Args:
            playlist_dir: Directory where playlists are stored
        """
        self._playlists = {}  # name -> tracks list
        self._on_playlists_change_callback = None
        self._playlist_dir = playlist_dir
        
        # Create playlist directory if it doesn't exist
        os.makedirs(self._playlist_dir, exist_ok=True)
        
        # Load existing playlists
        self._load_playlists()
    
    def _load_playlists(self) -> None:
        """Load all playlists from the playlists directory."""
        if not os.path.exists(self._playlist_dir):
            return
            
        for filename in os.listdir(self._playlist_dir):
            if filename.endswith('.json'):
                playlist_name = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self._playlist_dir, filename), 'r') as f:
                        playlist_data = json.load(f)
                        self._playlists[playlist_name] = playlist_data
                except Exception as e:
                    console.print(f"Error loading playlist {playlist_name}: {e}")
    
    def save_playlist(self, name: str) -> bool:
        """
        Save a playlist to disk.
        
        Args:
            name: Name of the playlist to save
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self._playlists:
            return False
            
        try:
            with open(os.path.join(self._playlist_dir, f"{name}.json"), 'w') as f:
                json.dump(self._playlists[name], f, indent=2)
            return True
        except Exception as e:
            console.print(f"Error saving playlist {name}: {e}")
            return False
    
    def create_playlist(self, name: str) -> bool:
        """
        Create a new empty playlist.
        
        Args:
            name: Name of the new playlist
            
        Returns:
            True if successful, False if playlist already exists
        """
        if name in self._playlists:
            return False
            
        self._playlists[name] = []
        self.save_playlist(name)
        self._notify_playlists_change()
        return True
    
    def delete_playlist(self, name: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            name: Name of the playlist to delete
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self._playlists:
            return False
            
        # Remove from memory
        del self._playlists[name]
        
        # Remove from disk
        try:
            playlist_path = os.path.join(self._playlist_dir, f"{name}.json")
            if os.path.exists(playlist_path):
                os.remove(playlist_path)
            self._notify_playlists_change()
            return True
        except Exception as e:
            console.print(f"Error deleting playlist {name}: {e}")
            return False
    
    def add_track_to_playlist(self, playlist_name: str, track: Dict) -> bool:
        """
        Add a track to a playlist.
        
        Args:
            playlist_name: Name of the playlist
            track: Track information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if playlist_name not in self._playlists:
            return False
            
        # Avoid duplicates by checking track IDs
        track_id = track.get('id')
        if track_id:
            # Check if track already exists in playlist
            for existing_track in self._playlists[playlist_name]:
                if existing_track.get('id') == track_id:
                    return False  # Track already in playlist
                    
        # Add track to playlist
        self._playlists[playlist_name].append(track)
        
        # Save the updated playlist
        self.save_playlist(playlist_name)
        self._notify_playlists_change()
        return True
    
    def remove_track_from_playlist(self, playlist_name: str, track_index: int) -> bool:
        """
        Remove a track from a playlist by index.
        
        Args:
            playlist_name: Name of the playlist
            track_index: Index of the track to remove
            
        Returns:
            True if successful, False otherwise
        """
        if playlist_name not in self._playlists:
            return False
            
        playlist = self._playlists[playlist_name]
        if not 0 <= track_index < len(playlist):
            return False
            
        # Remove track
        playlist.pop(track_index)
        
        # Save the updated playlist
        self.save_playlist(playlist_name)
        self._notify_playlists_change()
        return True
    
    def get_playlists(self) -> List[str]:
        """
        Get a list of all playlist names.
        
        Returns:
            List of playlist names
        """
        return list(self._playlists.keys())
    
    def get_playlist(self, name: str) -> Optional[List[Dict]]:
        """
        Get the tracks in a playlist.
        
        Args:
            name: Name of the playlist
            
        Returns:
            List of tracks or None if playlist doesn't exist
        """
        return self._playlists.get(name)
    
    def rename_playlist(self, old_name: str, new_name: str) -> bool:
        """
        Rename a playlist.
        
        Args:
            old_name: Current name of the playlist
            new_name: New name for the playlist
            
        Returns:
            True if successful, False otherwise
        """
        if old_name not in self._playlists or new_name in self._playlists:
            return False
            
        # Get the playlist data
        playlist_data = self._playlists[old_name]
        
        # Add with new name
        self._playlists[new_name] = playlist_data
        
        # Delete old playlist
        del self._playlists[old_name]
        
        # Save new playlist
        self.save_playlist(new_name)
        
        # Delete old playlist file
        try:
            old_path = os.path.join(self._playlist_dir, f"{old_name}.json")
            if os.path.exists(old_path):
                os.remove(old_path)
                
            self._notify_playlists_change()
            return True
        except Exception as e:
            console.print(f"Error renaming playlist {old_name}: {e}")
            return False
    
    def set_on_playlists_change_callback(self, callback: Callable) -> None:
        """
        Set callback for when playlists change.
        
        Args:
            callback: Function to call when playlists change
        """
        self._on_playlists_change_callback = callback
        
    def _notify_playlists_change(self) -> None:
        """Notify listeners that playlists have changed."""
        if self._on_playlists_change_callback:
            try:
                self._on_playlists_change_callback(self)
            except Exception as e:
                console.print(f"Error in playlists change callback: {e}")