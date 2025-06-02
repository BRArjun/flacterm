from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, DataTable, Label
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.message import Message
from textual.widget import Widget
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class PlaylistSelected(Message):
    """Message sent when a playlist is selected for adding a track."""
    def __init__(self, playlist: str) -> None:
        self.playlist = playlist
        super().__init__()

class PlaylistDisplay(Widget):
    """Widget for displaying and managing playlists."""
    
    def __init__(self, playlist_manager, id=None, classes=None):
        super().__init__(id=id, classes=classes)
        self.playlist_manager = playlist_manager
        self.selected_playlist = None
        self.viewing_playlist_tracks = False
        self.current_playlist_tracks = []
    
    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            with Vertical():
                # Header
                yield Label("🎵 Playlist Manager", id="playlist-header")
                
                # Create new playlist section
                with Horizontal(id="create-playlist-section"):
                    self.new_playlist_input = Input(
                        placeholder="Enter playlist name...",
                        id="new-playlist-input"
                    )
                    yield self.new_playlist_input
                    yield Button("Create", id="create-playlist-btn", variant="primary")
                
                # Playlist list/tracks display
                self.content_table = DataTable(id="playlist-content-table")
                self.content_table.cursor_type = "row"
                self.content_table.zebra_stripes = True
                self.content_table.show_cursor = True
                yield self.content_table
                
                # Action buttons
                with Horizontal(id="playlist-actions"):
                    yield Button("Back to Playlists", id="back-to-playlists-btn", classes="hidden")
                    yield Button("Delete Selected", id="delete-playlist-btn", variant="error")
                    yield Button("Rename", id="rename-playlist-btn")
                    yield Button("Clear Playlist", id="clear-playlist-btn", variant="warning")
                
                # Status info
                self.status_label = Label("", id="playlist-status")
                yield self.status_label
    
    def on_mount(self):
        """Initialize the display when mounted."""
        self.refresh_playlist_list()
    
    def refresh_playlist_list(self):
        """Refresh the playlist list display."""
        self.viewing_playlist_tracks = False
        self.selected_playlist = None
        self.current_playlist_tracks = []
        
        # Update table
        self.content_table.clear(columns=True)
        self.content_table.add_columns("Playlist Name", "Track Count", "Actions")
        
        playlists = self.playlist_manager.get_playlist_names()
        if not playlists:
            self.content_table.add_row("No playlists created", "0", "Create one above")
        else:
            for playlist_name in playlists:
                track_count = self.playlist_manager.get_playlist_count(playlist_name)
                self.content_table.add_row(
                    playlist_name,
                    str(track_count),
                    "Select to view tracks"
                )
        
        # Update UI state
        self.query_one("#back-to-playlists-btn").add_class("hidden")
        self.status_label.update(f"Total playlists: {len(playlists)}")
    
    def show_playlist_tracks(self, playlist_name: str):
        """Show tracks in the selected playlist."""
        self.viewing_playlist_tracks = True
        self.selected_playlist = playlist_name
        self.current_playlist_tracks = self.playlist_manager.get_playlist(playlist_name)
        
        # Update table
        self.content_table.clear(columns=True)
        self.content_table.add_columns("Title", "Artist", "Album", "Duration")
        
        if not self.current_playlist_tracks:
            self.content_table.add_row("No tracks in playlist", "Add some tracks", "", "")
        else:
            for track in self.current_playlist_tracks:
                duration = track.get("duration", 0)
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_str = f"{minutes}:{seconds:02d}"
                
                self.content_table.add_row(
                    track.get("title", "Unknown"),
                    track.get("artist", "Unknown"),
                    track.get("albumTitle", "Unknown"),
                    duration_str
                )
        
        # Update UI state
        self.query_one("#back-to-playlists-btn").remove_class("hidden")
        self.status_label.update(f"Playlist: {playlist_name} ({len(self.current_playlist_tracks)} tracks)")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-playlist-btn":
            self.create_playlist()
        elif event.button.id == "back-to-playlists-btn":
            self.refresh_playlist_list()
        elif event.button.id == "delete-playlist-btn":
            self.delete_selected()
        elif event.button.id == "rename-playlist-btn":
            self.rename_selected()
        elif event.button.id == "clear-playlist-btn":
            self.clear_selected()
    
    def create_playlist(self):
        """Create a new playlist."""
        name = self.new_playlist_input.value.strip()
        if not name:
            self.notify("Please enter a playlist name", title="Create Playlist")
            return
        
        if self.playlist_manager.create_playlist(name):
            self.new_playlist_input.value = ""
            self.refresh_playlist_list()
            self.notify(f"Created playlist: {name}", title="Success")
        else:
            self.notify(f"Failed to create playlist (may already exist)", title="Error")
    
    def delete_selected(self):
        """Delete the selected playlist or track."""
        if self.viewing_playlist_tracks:
            # Delete selected track from playlist
            if self.content_table.cursor_row is not None and self.current_playlist_tracks:
                track_index = self.content_table.cursor_row
                if 0 <= track_index < len(self.current_playlist_tracks):
                    track = self.current_playlist_tracks[track_index]
                    if self.playlist_manager.remove_track_from_playlist(self.selected_playlist, track_index):
                        self.show_playlist_tracks(self.selected_playlist)  # Refresh
                        self.notify(f"Removed track: {track.get('title', 'Unknown')}", title="Success")
                    else:
                        self.notify("Failed to remove track", title="Error")
        else:
            # Delete selected playlist
            if self.content_table.cursor_row is not None:
                playlists = self.playlist_manager.get_playlist_names()
                if 0 <= self.content_table.cursor_row < len(playlists):
                    playlist_name = playlists[self.content_table.cursor_row]
                    if self.playlist_manager.delete_playlist(playlist_name):
                        self.refresh_playlist_list()
                        self.notify(f"Deleted playlist: {playlist_name}", title="Success")
                    else:
                        self.notify("Failed to delete playlist", title="Error")
    
    def rename_selected(self):
        """Rename the selected playlist."""
        if self.viewing_playlist_tracks or self.content_table.cursor_row is None:
            self.notify("Select a playlist to rename", title="Rename")
            return
        
        playlists = self.playlist_manager.get_playlist_names()
        if 0 <= self.content_table.cursor_row < len(playlists):
            old_name = playlists[self.content_table.cursor_row]
            # For simplicity, we'll use the input field for the new name
            self.new_playlist_input.value = old_name
            self.new_playlist_input.focus()
            self.notify(f"Edit name in input field and press Create to rename '{old_name}'", title="Rename")
    
    def clear_selected(self):
        """Clear all tracks from selected playlist."""
        if self.viewing_playlist_tracks and self.selected_playlist:
            if self.playlist_manager.clear_playlist(self.selected_playlist):
                self.show_playlist_tracks(self.selected_playlist)  # Refresh
                self.notify(f"Cleared playlist: {self.selected_playlist}", title="Success")
            else:
                self.notify("Failed to clear playlist", title="Error")
        else:
            self.notify("Select a playlist to clear", title="Clear Playlist")
    
    def on_data_table_row_selected(self, event):
        """Handle row selection in the data table."""
        if not self.viewing_playlist_tracks:
            # User selected a playlist - show its tracks
            playlists = self.playlist_manager.get_playlist_names()
            if 0 <= event.cursor_row < len(playlists):
                playlist_name = playlists[event.cursor_row]
                self.show_playlist_tracks(playlist_name)
    
    def add_track_to_selected_playlist(self, track: dict) -> bool:
        """Add a track to the currently selected playlist."""
        if not self.selected_playlist:
            return False
        
        return self.playlist_manager.add_track_to_playlist(self.selected_playlist, track)
    
    def get_selected_playlist_name(self) -> str:
        """Get the name of the currently selected playlist."""
        return self.selected_playlist or ""
    
    def on_input_submitted(self, event):
        """Handle input submission."""
        if event.input.id == "new-playlist-input":
            self.create_playlist()