from textual.app import ComposeResult
from textual.widgets import Static, Button, DataTable, Label
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.message import Message

class PlaylistSelectionResult(Message):
    """Message sent when a playlist is selected."""
    def __init__(self, playlist_name: str, action: str) -> None:
        self.playlist_name = playlist_name
        self.action = action  # "add" or "remove"
        super().__init__()

class PlaylistSelectorModal(ModalScreen):
    """Modal screen for selecting a playlist to add/remove tracks."""
    
    def __init__(self, playlist_manager, track_title: str = "", action: str = "add"):
        super().__init__()
        self.playlist_manager = playlist_manager
        self.track_title = track_title
        self.action = action  # "add" or "remove"
    
    def compose(self) -> ComposeResult:
        with Vertical(id="playlist-selector-modal"):
            action_text = "Add to" if self.action == "add" else "Remove from"
            yield Label(f"{action_text} Playlist", id="modal-title")
            
            if self.track_title:
                yield Label(f"Track: {self.track_title}", id="track-info")
            
            # Playlist list
            self.playlist_table = DataTable(id="playlist-selector-table")
            self.playlist_table.cursor_type = "row"
            self.playlist_table.zebra_stripes = True
            self.playlist_table.show_cursor = True
            yield self.playlist_table
            
            # Action buttons
            with Horizontal(id="modal-buttons"):
                yield Button("Select", id="select-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")
    
    def on_mount(self):
        """Initialize the modal when mounted."""
        self.refresh_playlist_list()
        self.playlist_table.focus()
    
    def refresh_playlist_list(self):
        """Refresh the playlist list."""
        self.playlist_table.clear(columns=True)
        self.playlist_table.add_columns("Playlist Name", "Track Count")
        
        playlists = self.playlist_manager.get_playlist_names()
        if not playlists:
            self.playlist_table.add_row("No playlists available", "0")
        else:
            for playlist_name in playlists:
                track_count = self.playlist_manager.get_playlist_count(playlist_name)
                self.playlist_table.add_row(playlist_name, str(track_count))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "select-btn":
            self.select_playlist()
        elif event.button.id == "cancel-btn":
            self.dismiss()
    
    def on_data_table_row_selected(self, event):
        """Handle double-click on playlist row."""
        self.select_playlist()
    
    def select_playlist(self):
        """Select the highlighted playlist."""
        if self.playlist_table.cursor_row is not None:
            playlists = self.playlist_manager.get_playlist_names()
            if playlists and 0 <= self.playlist_table.cursor_row < len(playlists):
                selected_playlist = playlists[self.playlist_table.cursor_row]
                # Send result message to parent
                self.post_message(PlaylistSelectionResult(selected_playlist, self.action))
                self.dismiss()
            else:
                self.notify("No playlist selected", title="Selection Error")
        else:
            self.notify("Please select a playlist", title="No Selection")
    
    def on_key(self, event):
        """Handle key presses."""
        if event.key == "enter":
            self.select_playlist()
        elif event.key == "escape":
            self.dismiss()