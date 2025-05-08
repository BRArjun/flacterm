"""
Playlist display component for DAB Terminal Music Player.
Handles UI elements for playlist management.
"""
from textual.widgets import Static, DataTable, Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from rich.panel import Panel

from components.playlist_manager import PlaylistManager
from components.playlist_selector import PlaylistSelector

class PlaylistDisplay(Widget):
    """Widget for displaying and managing playlists."""
    
    DEFAULT_CSS = """
    #playlist-display {
        height: auto;
        max-height: 40vh;
        margin: 0;
        padding: 0;
        overflow-y: auto;
        border-top: solid #333;
    }
    
    #playlist-selector {
        height: 3;
        margin: 0 0 1 0;
    }
    
    #playlist-table {
        height: auto;
        max-height: 20vh;
    }
    
    .playlist-controls {
        height: 3;
        margin: 1 0;
    }
    
    .playlist-input {
        width: 60%;
    }
    
    .playlist-button {
        padding: 0 1;
        min-width: 10;
        color: $text;
        background: $boost;
        border: tall $primary;
    }
    
    .hidden {
        display: none;
    }
    """
    
    def __init__(self, playlist_manager: PlaylistManager, queue_manager=None, **kwargs):
        """
        Initialize the playlist display widget.
        
        Args:
            playlist_manager: The playlist manager instance
            queue_manager: Optional queue manager for playing playlists
        """
        super().__init__(**kwargs)
        self.playlist_manager = playlist_manager
        self.queue_manager = queue_manager
        self.current_playlist = None
        
        # Register for playlist updates
        self.playlist_manager.set_on_playlists_change_callback(self._on_playlists_change)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            # Top controls - playlist selection and creation
            with Horizontal(id="playlist-selector"):
                self.playlist_dropdown = Input(placeholder="Select a playlist", id="playlist-dropdown")
                yield self.playlist_dropdown
                yield Button("Load", id="load-playlist-btn", classes="playlist-button")
                yield Button("New", id="new-playlist-btn", classes="playlist-button")
                yield Button("Delete", id="delete-playlist-btn", classes="playlist-button")
            
            # New playlist creation area (hidden by default)
            with Horizontal(id="new-playlist-area", classes="playlist-controls hidden"):
                self.new_playlist_input = Input(placeholder="New playlist name", id="new-playlist-input", classes="playlist-input")
                yield self.new_playlist_input
                yield Button("Create", id="create-playlist-btn", classes="playlist-button")
                yield Button("Cancel", id="cancel-create-btn", classes="playlist-button")
            
            # Playlist contents table
            self.playlist_table = DataTable(id="playlist-table")
            yield self.playlist_table
            
            playlists = self.app.playlist_manager.get_playlists()
            yield PlaylistSelector(playlists)
            
            # Playlist action buttons
            with Horizontal(classes="playlist-controls"):
                yield Button("Play All", id="play-playlist-btn", classes="playlist-button")
                yield Button("Add to Queue", id="add-to-queue-btn", classes="playlist-button")
                yield Button("Remove Track", id="remove-track-btn", classes="playlist-button")
                yield Button("Rename", id="rename-playlist-btn", classes="playlist-button")
                
            # Rename playlist area (hidden by default)
            with Horizontal(id="rename-playlist-area", classes="playlist-controls hidden"):
                self.rename_playlist_input = Input(placeholder="New name", id="rename-playlist-input", classes="playlist-input")
                yield self.rename_playlist_input
                yield Button("Save", id="save-rename-btn", classes="playlist-button")
                yield Button("Cancel", id="cancel-rename-btn", classes="playlist-button")
    
    def on_mount(self) -> None:
        """Initialize UI components when mounted."""
        # Set up the playlist table
        self.playlist_table.add_columns("Title", "Artist", "Album", "Duration")
        self.playlist_table.cursor_type = "row"
        self.playlist_table.zebra_stripes = True
        
        # Update the playlist dropdown
        self._update_playlist_dropdown()
    
    def _update_playlist_dropdown(self) -> None:
        """Update the playlist dropdown with available playlists."""
        # In a real dropdown we'd populate options, but since we're using Input as a substitute:
        playlists = self.playlist_manager.get_playlists()
        if playlists:
            options = ", ".join(playlists)
            self.playlist_dropdown.placeholder = f"Available: {options}"
        else:
            self.playlist_dropdown.placeholder = "No playlists available"
    
    def _display_playlist(self, playlist_name: str) -> None:
        """
        Display the contents of a playlist in the table.
        
        Args:
            playlist_name: Name of the playlist to display
        """
        self.current_playlist = playlist_name
        playlist_tracks = self.playlist_manager.get_playlist(playlist_name)
        
        # Clear the table
        self.playlist_table.clear()
        
        if not playlist_tracks:
            # Add an empty row to show the playlist is empty
            self.playlist_table.add_row("No tracks in playlist", "", "", "")
            return
            
        # Add tracks to the table
        for track in playlist_tracks:
            duration = track.get("duration", 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
            
            self.playlist_table.add_row(
                track.get("title", "Unknown"),
                track.get("artist", "Unknown"),
                track.get("albumTitle", "Unknown"),
                duration_str
            )
    
    def _on_playlists_change(self, _) -> None:
        """Callback when playlists change."""
        self._update_playlist_dropdown()
        
        # If we have a current playlist loaded, refresh it
        if self.current_playlist:
            self._display_playlist(self.current_playlist)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "load-playlist-btn":
            playlist_name = self.playlist_dropdown.value
            if playlist_name and self.playlist_manager.get_playlist(playlist_name) is not None:
                self._display_playlist(playlist_name)
            else:
                self.notify(f"Playlist '{playlist_name}' not found")
                
        elif button_id == "new-playlist-btn":
            # Show the new playlist input area
            self.query_one("#new-playlist-area").remove_class("hidden")
            self.query_one("#new-playlist-input").focus()
            
        elif button_id == "create-playlist-btn":
            # Create the new playlist
            new_name = self.new_playlist_input.value.strip()
            if new_name:
                if self.playlist_manager.create_playlist(new_name):
                    self.notify(f"Created playlist: {new_name}")
                    self.current_playlist = new_name
                    self._display_playlist(new_name)
                    # Hide the new playlist area
                    self.query_one("#new-playlist-area").add_class("hidden")
                    self.new_playlist_input.value = ""
                else:
                    self.notify(f"Playlist '{new_name}' already exists")
            else:
                self.notify("Please enter a playlist name")
                
        elif button_id == "cancel-create-btn":
            # Hide the new playlist area
            self.query_one("#new-playlist-area").add_class("hidden")
            self.new_playlist_input.value = ""
            
        elif button_id == "delete-playlist-btn":
            # Delete the current playlist
            if self.current_playlist:
                if self.playlist_manager.delete_playlist(self.current_playlist):
                    self.notify(f"Deleted playlist: {self.current_playlist}")
                    self.current_playlist = None
                    self.playlist_table.clear()
                else:
                    self.notify(f"Failed to delete playlist: {self.current_playlist}")
            else:
                self.notify("No playlist selected")
                
        elif button_id == "play-playlist-btn":
            # Play all tracks in the current playlist
            if not self.current_playlist or not self.queue_manager:
                self.notify("No playlist selected or queue manager not available")
                return
                
            playlist_tracks = self.playlist_manager.get_playlist(self.current_playlist)
            if not playlist_tracks:
                self.notify("Playlist is empty")
                return
                
            # Clear queue and add all tracks
            self.queue_manager.clear_queue()
            for track in playlist_tracks:
                self.queue_manager.add_track(track)
                
            self.notify(f"Added {len(playlist_tracks)} tracks to queue from '{self.current_playlist}'")
                
        elif button_id == "add-to-queue-btn":
            # Add the selected track to the queue
            if not self.current_playlist or not self.queue_manager:
                self.notify("No playlist selected or queue manager not available")
                return
                
            # Get the selected track index
            selected_row = self.playlist_table.cursor_row
            if selected_row is None:
                self.notify("No track selected")
                return
                
            playlist_tracks = self.playlist_manager.get_playlist(self.current_playlist)
            if not playlist_tracks or selected_row >= len(playlist_tracks):
                self.notify("Invalid track selection")
                return
                
            # Add the track to the queue
            track = playlist_tracks[selected_row]
            self.queue_manager.add_track(track)
            self.notify(f"Added '{track.get('title', 'Unknown')}' to queue")
                
        elif button_id == "remove-track-btn":
            # Remove the selected track from the playlist
            if not self.current_playlist:
                self.notify("No playlist selected")
                return
                
            # Get the selected track index
            selected_row = self.playlist_table.cursor_row
            if selected_row is None:
                self.notify("No track selected")
                return
                
            if self.playlist_manager.remove_track_from_playlist(self.current_playlist, selected_row):
                self.notify(f"Removed track from '{self.current_playlist}'")
                # Refresh the display
                self._display_playlist(self.current_playlist)
            else:
                self.notify("Failed to remove track")
                
        elif button_id == "rename-playlist-btn":
            # Show the rename playlist input area
            if not self.current_playlist:
                self.notify("No playlist selected")
                return
                
            self.query_one("#rename-playlist-area").remove_class("hidden")
            self.rename_playlist_input.value = self.current_playlist
            self.rename_playlist_input.focus()
            
        elif button_id == "save-rename-btn":
            # Rename the current playlist
            if not self.current_playlist:
                self.notify("No playlist selected")
                return
                
            new_name = self.rename_playlist_input.value.strip()
            if not new_name:
                self.notify("Please enter a new playlist name")
                return
                
            if self.playlist_manager.rename_playlist(self.current_playlist, new_name):
                self.notify(f"Renamed playlist to '{new_name}'")
                self.current_playlist = new_name
                # Hide the rename area
                self.query_one("#rename-playlist-area").add_class("hidden")
            else:
                self.notify(f"Failed to rename playlist or '{new_name}' already exists")
                
        elif button_id == "cancel-rename-btn":
            # Hide the rename playlist area
            self.query_one("#rename-playlist-area").add_class("hidden")
    
    def add_current_track_to_playlist(self, track, playlist_name=None) -> bool:
        """
        Add the currently playing track to a playlist.
        
        Args:
            track: Track to add
            playlist_name: Optional playlist name, if None will use current playlist
            
        Returns:
            True if successful, False otherwise
        """
        target_playlist = playlist_name or self.current_playlist
        if not target_playlist:
            self.notify("No playlist selected")
            return False
            
        if self.playlist_manager.add_track_to_playlist(target_playlist, track):
            self.notify(f"Added '{track.get('title', 'Unknown')}' to '{target_playlist}'")
            # Refresh the display if we're viewing this playlist
            if target_playlist == self.current_playlist:
                self._display_playlist(self.current_playlist)
            return True
        else:
            self.notify(f"Failed to add track to '{target_playlist}' or track already exists")
            return False