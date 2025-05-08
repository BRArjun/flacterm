from textual.widgets import Input, ListView, Label, ListItem
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.app import ComposeResult
from textual import events

class PlaylistSelected(Message):
    """Message sent when a playlist is selected."""
    
    def __init__(self) -> None:
        super().__init__()
        self.playlist = ""  # Will be set after initialization
        
    @classmethod
    def from_selection(cls, sender, playlist: str):
        """Create a message from a selection."""
        message = cls()
        message.playlist = playlist
        return message

class PlaylistSelector(Vertical):
    playlists = reactive(list)
    matches = reactive(list)
    input_value = reactive("")
    selected_index = reactive(0)

    def __init__(self, playlists: list[str]) -> None:
        super().__init__()
        self.playlists = playlists
        self.matches = playlists.copy()  # Initialize matches with all playlists

    def compose(self) -> ComposeResult:
        # Create the input widget
        yield Input(placeholder="Select playlist...", id="playlist-input")
        # Create and yield the ListView - initially empty
        yield ListView(id="playlist-list")

    def on_mount(self):
        # Focus the input field on mount
        self.query_one(Input).focus()
        # Now populate the list view with initial items
        self.update_list()

    def on_input_changed(self, event: Input.Changed):
        # Update input value and match playlists based on input
        self.input_value = event.value
        self.matches = [p for p in self.playlists if self.input_value.lower() in p.lower()]
        self.update_list()
        # Reset selected index when filter changes
        self.selected_index = 0

    def update_list(self):
        # Update the list of matching playlists in the ListView
        list_view = self.query_one(ListView)
        # Clear and repopulate the list
        list_view.clear()
        for match in self.matches:
            # Create a ListItem with a Label inside it
            list_item = ListItem(Label(match))
            list_view.append(list_item)
        
        # Update highlight if items exist
        if self.matches and list_view.index is None:
            list_view.index = 0

    def on_key(self, event: events.Key):
        """Handle key presses for navigation"""
        list_view = self.query_one(ListView)
        input_widget = self.query_one(Input)
        
        # If we have matches
        if self.matches:
            if event.key == "down":
                # Move focus to list if input is focused
                if input_widget.has_focus:
                    input_widget.blur()
                    list_view.focus()
                    list_view.index = 0
                # Otherwise navigate within list
                else:
                    if list_view.index < len(self.matches) - 1:
                        list_view.index += 1
                event.prevent_default()
            
            elif event.key == "up":
                # Move focus back to input if at top of list
                if list_view.has_focus and (list_view.index == 0 or list_view.index is None):
                    list_view.blur()
                    input_widget.focus()
                # Otherwise navigate within list
                elif list_view.has_focus:
                    list_view.index -= 1
                event.prevent_default()
            
            elif event.key == "enter":
                # If list has focus, select the current item
                if list_view.has_focus and list_view.index is not None:
                    self.select_playlist(self.matches[list_view.index])
                # If input has focus, select first match
                elif self.matches:
                    self.select_playlist(self.matches[0])
                event.prevent_default()
            
            elif event.key == "escape":
                # Clear input and reset
                input_widget.value = ""
                input_widget.focus()
                event.prevent_default()

    def on_list_view_selected(self, event: ListView.Selected):
        # Handle list selection
        if event.list_view.index is not None and 0 <= event.list_view.index < len(self.matches):
            playlist_name = self.matches[event.list_view.index]
            self.select_playlist(playlist_name)

    def select_playlist(self, playlist: str):
        """Helper method to emit selection message"""
        message = PlaylistSelected.from_selection(self, playlist)
        self.post_message(message)