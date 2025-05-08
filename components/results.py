from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Input
from textual.scroll_view import ScrollView
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import ScrollableContainer, Vertical, Container, Horizontal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from math import ceil
import threading
import time
import os
import re
import asyncio

from components.audio_player import AudioPlayer
from components.lyrics_display import LyricsDisplay
from components.keybinds_display import KeybindsDisplay
from utils.api import (
    fetch_all_results,
    get_streaming_url,
    get_track_detail,
    get_base_url,
    download_track
)

from components.queue_manager import QueueManager
from components.queue_display import QueueDisplay
from components.playlist_manager import PlaylistManager
from components.playlist_display import PlaylistDisplay
from components.playlist_selector import PlaylistSelector, PlaylistSelected


# Constants
ITEMS_PER_PAGE = 10
console = Console()

class Results(App):
    CSS = """
#progress_container {
  dock: bottom;
  height: 2;
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
}

#progress_visual {
  width: 100%;
  height: 1;
  content-align: center middle;
  color: $text-muted;
  background: transparent;
  padding: 0;
  margin: 0;
}

#progress_bar {
  dock: bottom;
  text-align: center;
  height: 1;
  background: transparent;
  color: white;
  width: 100%;
  padding: 0;
  margin: 0;
}

/* Style for the timestamp when playing */
.playing {
  color: $success;
}

.paused {
  color: $warning;
}

#footer {
  dock: bottom;
}

/* Ensure there's space between the table and the timestamp display */
#results_table {
  margin-bottom: 1;
}

#queue-display {
  height: auto;
  max-height: 40vh; /* Adjust height as needed */
  margin: 0;
  padding: 0;
  overflow-y: auto;
  display: block;
  border-top: solid #333;
}

/* Hide queue when not active */
#queue-display.hidden {
  display: none;
}

/* Additional styles for queue items */
.queue-item {
  padding: 1 2;
}

.queue-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.queue-item.current {
  background: rgba(255, 255, 255, 0.1);
  text-style: bold;
}

/* Empty queue message */
.empty-queue {
  text-align: center;
  padding: 5;
  color: #888;
}

/* Queue panel title */
#queue-display Panel {
  border: round;
}
"""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "show_info", "Show Info"),
        ("/", "search", "New Search"),
        ("n", "next_page", "Next Page"),
        ("p", "prev_page", "Prev Page"),
        ("space", "toggle_play", "Play/Pause"),
        ("escape", "stop_playback", "Stop"),
        ("h", "fast_forward", "Forward"),
        ("g", "rewind", "Rewind"),
        ("ctrl+s", "submit_search", "Submit Search"),
        ("l", "toggle_lyrics", "Show/Hide Lyrics"),
        ("r", "toggle_repeat", "Repeat Mode"),
        ("v", "toggle_keybinds", "Toggle keybindings help"),
        ("d", "download_hovered_track", "Download Track"),
        ("a", "add_to_queue", "Add to queue"),
        ("t", "toggle_queue", "Toggle queue"),
        ("y", "remove_from_queue", "Remove from Queue"),
        ("z", "next_track", "Next Track"),
        ("x", "previous_track", "Previous Track"),
        ("c", "clear_queue", "Clear Queue"),
        ("tab", "focus_next", "Switch panel focus"),
        ("m", "toggle_playlists", "Toggle playlists"),
        ("w", "add_to_playlist", "Add to playlist"),
    ]

    def __init__(self, results=None, search_type="track", query=""):
        super().__init__()
        self.results = results or []
        self.search_type = search_type
        self.query = query
        self.current_track_info = None
        self.showing_info = False
        self.current_page = 0
        self.total_pages = ceil(len(self.results) / ITEMS_PER_PAGE) if self.results else 0
        self.player = AudioPlayer()
        self.currently_playing = None
        self.is_paused = False
        self.repeat = False
        self.lyrics_display = None
        self.progress_bar_content = None
        self.progress_ticker = None  # For regular UI updates
        self.displayed_results = []  # To keep track of currently displayed results
        # Initialize queue manager
        self.queue_manager = QueueManager()
        # Track visibility of queue
        self.show_queue = False
        self.playlist_manager = PlaylistManager()
        self.show_playlists = False
        
    def compose(self) -> ComposeResult:
        yield Header(f"DAB Terminal - Search: '{self.query}'")

        # Main vertical layout
        with Vertical():
            self.search_input = Input(placeholder="Search for a new track...", id="search_input")
            self.search_input.styles.display = "none"
            yield self.search_input

            self.keybinds_display = KeybindsDisplay(id="keybinds_display")
            self.keybinds_display.styles.display = "none"
            yield self.keybinds_display

            self.now_playing = Static("Not Playing", id="now_playing")
            yield self.now_playing

            self.lyrics_display = LyricsDisplay(id="lyrics_display")
            self.lyrics_display.styles.display = "none"
            yield self.lyrics_display

            self.table = DataTable(id="results_table")
            yield self.table

            yield DataTable(id="queue_table")

            self.pagination = Static(id="pagination")
            yield self.pagination

            self.info = Static("", id="info")
            yield self.info

            yield QueueDisplay(self.queue_manager, id="queue-display", classes="hidden")

            yield PlaylistDisplay(self.playlist_manager, self.queue_manager, id="playlist-display", classes="hidden")

        # Docked progress bar at the bottom
        with Container(id="progress_container"):
            yield Static("", id="progress_bar")  # This gets updated with timestamp + bar

    def on_mount(self):
        """Set up the UI when the app is mounted."""
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.table.show_cursor = True
        self.table.focus()
        self.update_page()

        self.keybinds_display = self.query_one("#keybinds_display")
        self.keybinds_display.styles.display = "none"

        self.lyrics_display = self.query_one("#lyrics_display")
        self.lyrics_display.styles.display = "none"

        self.player.set_position_callback(self.update_progress)
        self.player.set_on_end_callback(self.on_track_end)

        self.set_interval(0.5, self.check_progress_updates)

        self.query_one("#queue-display").display = False

        self.query_one("#playlist-display").display = False
        
    def check_progress_updates(self):
        """Regular timer callback to ensure progress bar updates."""
        if self.player.is_currently_playing():
            position = self.player.get_current_time()
            duration = self.player.get_duration()
            if duration > 0:
                self._update_progress_ui(position, duration)
    
    def play_track(self, track):
        """Play a track and update the UI accordingly."""
        track_id = track.get("id")
        if not track_id:
            self.notify("No track ID found", title="Play Error")
            return
        
        self.stop_playback()
        stream_url = get_streaming_url(track_id)
        if not stream_url:
            self.notify("No streaming URL found", title="Play Error")
            return
            
        # Add stream URL to track info for convenience
        track['stream_url'] = stream_url
            
        # Store current track info
        self.currently_playing = track
        self.is_paused = False
        
        # Update UI to show what's playing
        repeat_status = "[Repeat ON]" if self.repeat else ""
        self.now_playing.update(f"Now Playing: {track.get('title')} - {track.get('artist')} {repeat_status}")
        
        # Start playback using the URL
        self.player.play(stream_url)
        
        # Fetch lyrics if the lyrics display is visible
        if self.lyrics_display.styles.display != "none":
            artist = track.get("artist", "")
            title = track.get("title", "")
            self.lyrics_display.fetch_lyrics(artist, title)
        
        self.notify(f"Playing: {track.get('title')}", title="Now Playing")
    
    def update_progress(self, position, duration):
        """Callback for audio player to update progress."""
        if duration == 0:
            percent = 0
        else:
            percent = position / duration

        # Call UI update from player thread
        self.call_from_thread(lambda: self._update_progress_ui(position, duration))

    def _update_progress_ui(self, position, duration):
        """Updates the UI components on the main thread."""
        try:
            progress_bar = self.query_one("#progress_bar", Static)
            if not progress_bar:
                return
            width = progress_bar.size.width or 80  # Fallback if width not yet known
        except Exception:
            width = 80

        bar_width = max(width - 20, 10)  # Leave room for time text
        percent = min(position / duration, 1.0) if duration > 0 else 0
        filled = int(bar_width * percent)
        empty = bar_width - filled
        bar = f"▕{'█' * filled}{'░' * empty}▏"

        minutes_pos, seconds_pos = divmod(int(position), 60)
        minutes_dur, seconds_dur = divmod(int(duration), 60)
        status = "(Paused)" if self.is_paused else "(Playing)"
        if not self.currently_playing:
            status = "(Not Playing)"

        time_text = f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d} {status}"
        progress_text = f"{bar} {time_text}"

        progress_bar.update(progress_text)

        if hasattr(self, 'lyrics_display') and self.lyrics_display.styles.display != "none":
            self.lyrics_display.update_position(position)

    def get_selected_track(self):
        """
        Get the currently selected track from the data table.
        Returns:
            A track dictionary from self.displayed_results or None.
        """
        if self.table.cursor_row is not None:
            index = self.table.cursor_row
            if 0 <= index < len(self.displayed_results):
                return self.displayed_results[index]
        return None

    def on_track_end(self):
        """Handle end of track by playing the next track in queue if available."""
        # Check if we should automatically play the next track
        next_track = self.queue_manager.next_track()
        if next_track:
            self.play_track(next_track)

    def stop_playback(self):
        if self.currently_playing:
            self.player.stop()
            self.currently_playing = None
            self.is_paused = False
            self.now_playing.update("Not Playing")
            self.notify("Playback stopped", title="Playback")

    def _handle_track_end(self):
        """Handle track end in the main thread."""
        
        # Use existing logic for repeat functionality
        if self.repeat and self.currently_playing:
            self.play_track(self.currently_playing)
        else:
            self.currently_playing = None
            self.now_playing.update("Not Playing")

    def update_page(self):
        """Update the data table with the current page of results."""
        self.table.clear(columns=True)
        self.table.add_columns("Title", "Artist", "Album", "Duration")
        
        start_idx = self.current_page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(self.results))
        
        # Store displayed results for easy access
        self.displayed_results = self.results[start_idx:end_idx]
        
        for item in self.displayed_results:
            duration = item.get("duration", 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
            self.table.add_row(
                item.get("title", "Unknown"), 
                item.get("artist", "Unknown"), 
                item.get("albumTitle", "Unknown"), 
                duration_str
            )
            
        pagination_text = f"Page {self.current_page + 1}/{self.total_pages} | Items {start_idx + 1}-{end_idx} of {len(self.results)}"
        self.pagination.update(pagination_text)
        
        # Reset info panel
        self.showing_info = False
        self.info.update("")
        self.info.styles.height = 1

    def action_next_page(self):
        """Navigate to the next page of results."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()

    def action_focus_next(self) -> None:
        """Toggle focus between results and queue tables."""
        results_table = self.query_one("#results_table", DataTable)
        queue_table = self.query_one("#queue_table", DataTable)

        if self.focused == results_table:
            self.set_focus(queue_table)
        else:
            self.set_focus(results_table)

    def action_focus_queue(self):
        self.set_focus(self.query_one("#queue"))

    def action_focus_results(self):
        self.set_focus(self.query_one("#results"))

    def action_next_track(self):
        """Play the next track in the queue."""
        next_track = self.queue_manager.next_track()
        if next_track:
            self.play_track(next_track)
        else:
            self.notify("No more tracks in queue")
    
    def action_previous_track(self):
        """Play the previous track in the queue."""
        prev_track = self.queue_manager.previous_track()
        if prev_track:
            self.play_track(prev_track)
        else:
            self.notify("No previous tracks in queue")
    
    def action_clear_queue(self):
        """Clear the queue."""
        self.queue_manager.clear_queue()
        self.notify("Queue cleared")
    
    def action_prev_page(self):
        """Navigate to the previous page of results."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def action_play_selected(self):
        """Play the currently selected track."""
        row_index = self.table.cursor_row
        if 0 <= row_index < len(self.displayed_results):
            self.play_track(self.displayed_results[row_index])

    def action_toggle_play(self):
        """Handle play/pause action."""
        if not self.currently_playing:
            # Nothing is playing, so try to play the selected track
            self.action_play_selected()
        else:
            # Toggle pause/resume on currently playing track
            if self.is_paused:
                self.player.resume()
                self.is_paused = False
                self.notify("Playback resumed", title="Playback")
            else:
                self.player.pause()
                self.is_paused = True
                self.notify("Playback paused", title="Playback")

    def action_toggle_queue(self):
        """Toggle the queue display visibility."""
        queue_display = self.query_one("#queue-display")
        self.show_queue = not self.show_queue
        
        if self.show_queue:
            queue_display.remove_class("hidden")
            queue_display.display = True
        else:
            queue_display.add_class("hidden")
            queue_display.display = False
    
    def action_add_to_queue(self):
        """Add the currently selected track to the queue."""
        # Get the currently selected track from your existing selection mechanism
        selected_track = self.get_selected_track()  # You'll need to implement this based on your UI
        
        if selected_track:
            self.queue_manager.add_track(selected_track)
            self.notify(f"Added '{selected_track.get('title', 'Unknown')}' to queue")
    
    def action_remove_from_queue(self):
        """Remove a track from the queue."""
        # This might need to prompt the user for which track to remove
        # or remove the currently highlighted track in the queue
        if not self.queue_manager.queue:
            self.notify("Queue is empty")
            return
        
        # For simplicity, remove the currently playing track
        # In a real implementation, you might want to highlight and select tracks in the queue
        if self.queue_manager.current_index >= 0:
            track = self.queue_manager.current_track
            self.queue_manager.remove_track(self.queue_manager.current_index)
            self.notify(f"Removed '{track.get('title', 'Unknown')}' from queue")
        else:
            self.notify("No track selected in queue")

    def action_stop_playback(self):
        """Stop the current playback."""
        if self.currently_playing:
            self.player.stop()
            self.currently_playing = None
            self.is_paused = False
            self.now_playing.update("Not Playing")
            
            # Update progress bar
            progress_bar = self.query_one("#progress_bar", Static)
            progress_bar.update("▕░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▏ 0:00 / 0:00 (Not Playing)")
            
            self.notify("Playback stopped", title="Playback")
            
        # Hide lyrics display if showing
        if self.lyrics_display and self.lyrics_display.styles.display != "none":
            self.lyrics_display.styles.display = "none"
    
    def get_current_playback_position(self):
        """Return current playback time in seconds from player."""
        return self.player.get_current_time()

    def action_fast_forward(self):
        """Fast forward 5 seconds."""
        if self.player.is_playing:
            current_time = self.player.player.get_time()
            new_time = current_time + 5000  # 5 seconds
            duration = self.player.player.get_length()
            if new_time < duration:
                self.player.player.set_time(new_time)
                self.notify("Fast forwarded 5 seconds", title="Seek")
    
    def action_rewind(self):
        """Rewind 5 seconds."""
        if self.player.is_playing:
            current_time = self.player.player.get_time()
            new_time = max(0, current_time - 5000)
            self.player.player.set_time(new_time)
            self.notify("Rewound 5 seconds", title="Seek")
    
    def action_toggle_repeat(self):
        """Toggle repeat mode."""
        self.repeat = not self.repeat
        repeat_status = "ON" if self.repeat else "OFF"
        self.notify(f"Repeat mode: {repeat_status}", title="Repeat Mode")
        
        if self.currently_playing:
            self.now_playing.update(f"Now Playing: {self.currently_playing.get('title')} - {self.currently_playing.get('artist')} [Repeat {repeat_status}]")
    
    def action_search(self):
        """Show or hide the search input box."""
        if self.search_input.styles.display == "none":
            self.search_input.styles.display = "block"
            self.set_focus(self.search_input)
        else:
            self.search_input.styles.display = "none"
            self.set_focus(self.table)
    
    def action_submit_search(self):
        """Process the search input and fetch results."""
        query = self.search_input.value.strip()
        if not query:
            self.search_input.styles.display = "none"
            self.set_focus(self.table)
            return

        self.stop_playback()
        self.search_input.styles.display = "none"
        self.set_focus(self.table)
        self.query = query

        # Show loading indicator
        self.pagination.update("Searching...")

        def do_search():
            """Background thread to perform search"""
            new_results = fetch_all_results(query, self.search_type)
            if not new_results:
                self.call_from_thread(lambda: self.notify("No results found", title="Search"))
                self.call_from_thread(lambda: self.pagination.update("No results found"))
                return

            def update_ui():
                self.results = new_results
                self.current_page = 0
                self.total_pages = ceil(len(self.results) / ITEMS_PER_PAGE)
                self.update_page()
                self.set_title(f"DAB Terminal - Search: '{self.query}'")

            self.call_from_thread(update_ui)

        threading.Thread(target=do_search, daemon=True).start()

    async def action_toggle_keybinds(self):
        """Toggle visibility of the keybinds help screen."""
        if not hasattr(self, "keybinds_display") or self.keybinds_display is None:
            self.keybinds_display = self.query_one("#keybinds_display", Static)
            if not self.keybinds_display:
                self.notify("Keybinds display not available", title="Error")
                return

        if self.keybinds_display.styles.display == "none":
            self.keybinds_display.styles.display = "block"
            self.notify("Showing keybindings", title="Help")
        else:
            self.keybinds_display.styles.display = "none"
            self.notify("Hiding keybindings", title="Help")

    def action_toggle_playlists(self):
        """Toggle the playlist display visibility."""
        playlist_display = self.query_one("#playlist-display")
        self.show_playlists = not self.show_playlists
        
        if self.show_playlists:
            playlist_display.remove_class("hidden")
            playlist_display.display = True
        else:
            playlist_display.add_class("hidden")
            playlist_display.display = False
    
    def action_add_to_playlist(self):
        """Add the currently selected track to a playlist."""
        selected_track = self.get_selected_track()
        if not selected_track:
            self.notify("No track selected")
            return

        track_to_add = self.currently_playing or selected_track
        playlists = self.playlist_manager.get_playlists()

        playlist_display = self.query_one("#playlist-display")

        if not playlists:
            self.notify("No playlists available. Create one first.")
            self.show_playlists = True
            playlist_display.remove_class("hidden")
            
            # Show the new playlist creation form automatically
            playlist_display.query_one("#new-playlist-area").remove_class("hidden")
            playlist_display.query_one("#new-playlist-input").focus()

            return

        # Use the first playlist for simplicity
        playlist_name = playlists[0]
        if playlist_display.add_current_track_to_playlist(track_to_add, playlist_name):
            self.notify(f"Added '{track_to_add.get('title', 'Unknown')}' to playlist '{playlist_name}'")
        else:
            self.notify("Failed to add track to playlist")

    def on_playlist_selected(self, event: PlaylistSelected):
        selected_track = self.get_selected_track()
        if not selected_track:
            self.notify("No track selected")
            return

        track_to_add = self.currently_playing or selected_track
        playlist_name = event.playlist

        playlist_display = self.query_one("#playlist-display")
        if playlist_display.add_current_track_to_playlist(track_to_add, playlist_name):
            self.notify(f"Added '{track_to_add.get('title', 'Unknown')}' to playlist '{playlist_name}'")
        else:
            self.notify("Failed to add track to playlist")

        # Optionally hide the selector again
        self.show_playlists = False
        playlist_display.add_class("hidden")

    async def action_download_hovered_track(self):
        """Download the hovered track from results table."""
        if not self.table or not self.results:
            self.notify("No table or results loaded", title="Error")
            return

        cursor_row = self.table.cursor_row
        if cursor_row is None or cursor_row >= len(self.displayed_results):
            self.notify("Invalid selection", title="Download Failed")
            return

        track = self.displayed_results[cursor_row]
        track_id = track.get("id")
        title = track.get("title", "Unknown Track")

        if not track_id:
            self.notify("Track ID missing.", title="Download Failed")
            return

        # Pause playback if needed
        was_playing = False
        if self.player and self.player.is_playing:
            was_playing = True
            self.player.pause()

        # Notify that download has started
        self.notify(f"Downloading {title}...", title="Download", timeout=3)

        def on_download_complete():
            self.notify(f"✅ Download complete: {title}", title="Finished", timeout=5)
            if was_playing:
                self.player.resume()

        def background_download():
            try:
                file_path = download_track(track_id)
                if not file_path:
                    raise ValueError("Failed to get streaming URL")

                # Wait for the file to be fully written
                while not os.path.exists(file_path) or os.path.getsize(file_path) < 10000:
                    time.sleep(0.2)

                on_download_complete()
            except Exception as e:
                self.notify(f"❌ Download failed: {e}", title="Error", timeout=5)
                if was_playing:
                    self.player.resume()

        threading.Thread(target=background_download, daemon=True).start()

    def format_track_info(self, track):
        """Format track details into a rich table."""
        track_id = track.get("id")
        if track_id:
            detailed_info = get_track_detail(track_id)
            if detailed_info:
                track.update(detailed_info)

        duration = track.get("duration", 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}:{seconds:02d}"

        # Extract audio details
        bit_depth = track.get("audioQuality", {}).get("maximumBitDepth", 0)
        sample_rate_khz = track.get("audioQuality", {}).get("maximumSamplingRate", 0)
        sample_rate_hz = int(sample_rate_khz * 1000)
        channels = track.get("maximumChannelCount", 2)

        # Approximate bitrate in kbps (bits per second / 1000)
        bitrate = (sample_rate_hz * bit_depth * channels) // 1000 if all([bit_depth, sample_rate_khz, channels]) else None

        # Format type
        format_type = "FLAC" if track.get("audioQuality", {}).get("isHiRes") else "Unknown"

        # Label and other metadata
        label = track.get("label", "Unknown")
        release_date = track.get("releaseDate", "Unknown")
        genre = track.get("genre", "Unknown")

        # Build output table
        table = Table(expand=True, box=None)
        table.add_column("Property")
        table.add_column("Value")
        table.add_row("Title", track.get("title", "Unknown"))
        table.add_row("Artist", track.get("artist", "Unknown"))
        table.add_row("Album", track.get("albumTitle", "Unknown"))
        table.add_row("Duration", duration_str)
        table.add_row("Release Date", release_date)
        table.add_row("Genre", genre)
        if bitrate:
            table.add_row("Bitrate", f"{bitrate} kbps")
        table.add_row("Format", format_type)
        table.add_row("Sample Rate", f"{sample_rate_hz} Hz")
        table.add_row("Label", label)

        return table

    def action_show_info(self):
        """Show or hide detailed information about the selected track."""
        row_index = self.table.cursor_row
        if 0 <= row_index < len(self.displayed_results):
            track = self.displayed_results[row_index]
            self.showing_info = not self.showing_info
            
            if self.showing_info:
                # Show loading indicator
                self.info.update("Loading track details...")
                self.info.styles.height = "auto"
                
                # Fetch detailed track info in background thread to avoid UI freezing
                def fetch_and_display_info():
                    track_info_table = self.format_track_info(track)
                    track_info_panel = Panel(
                        track_info_table, 
                        title=f"Track Info: {track.get('title', 'Unknown')}", 
                        border_style="green"
                    )
                    
                    # Update UI from main thread
                    self.call_from_thread(lambda: self.info.update(track_info_panel))
                
                threading.Thread(target=fetch_and_display_info, daemon=True).start()
            else:
                self.info.update("")  # Clear the panel content
                self.info.styles.height = 1

    def action_toggle_lyrics(self):
        """Toggle the visibility of lyrics display."""
        if not hasattr(self, 'lyrics_display') or self.lyrics_display is None:
            self.lyrics_display = self.query_one("#lyrics_display")
            if not self.lyrics_display:
                self.notify("Lyrics display not available", title="Error")
                return

        if not isinstance(self.lyrics_display, LyricsDisplay):
            old_display = self.lyrics_display
            self.lyrics_display = LyricsDisplay(id="lyrics_display_new")
            if old_display.parent:
                old_display.parent.mount(self.lyrics_display, before=old_display)
                old_display.remove()
            self.lyrics_display.styles.display = "none"

        if self.lyrics_display.styles.display == "none":
            if self.currently_playing:
                self.lyrics_display.styles.display = "block"
                artist = self.currently_playing.get("artist", "")
                title = self.currently_playing.get("title", "")
                
                # Fetch lyrics (sync highlighting is handled via update_position elsewhere)
                self.lyrics_display.fetch_lyrics(artist, title)
                self.notify("Showing lyrics", title="Lyrics")
            else:
                self.notify("No track currently playing", title="Lyrics")
        else:
            self.lyrics_display.styles.display = "none"
            self.notify("Hiding lyrics", title="Lyrics")

    def on_input_submitted(self, event):
        """Handle input submission event."""
        if event.input.id == "search_input":
            self.action_submit_search()

    def on_unmount(self):
        """Clean up resources when the app is closing."""
        self.player.stop()

    def action_quit(self):
        """Exit the application."""
        self.exit()