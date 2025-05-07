import requests
import json
import base64
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from urllib.parse import urlencode
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.scroll_view import ScrollView
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import ScrollableContainer
from textual.containers import Vertical, Container
from math import ceil
import vlc
import re
import threading
import time
from rich.text import Text
from textual.widgets import Input
from textual.containers import Horizontal
from textual.widgets import Static
import asyncio
from urllib.parse import quote

# Constants
ITEMS_PER_PAGE = 10
_ENCODED_API = b'aHR0cHM6Ly9kYWIueWVldC5zdS9hcGk='
console = Console()

def get_base_url():
    return base64.b64decode(_ENCODED_API).decode('utf-8')

class AudioPlayer:
    def __init__(self):
        # Initialize VLC instance and player
        self.instance = vlc.Instance('--no-xlib')
        self.player = self.instance.media_player_new()
        self.media = None
        self.is_playing = False
        self.is_paused = False
        self._position_callback = None
        self._on_end_callback = None
        self._update_thread = None
        self._running = False
        
    def play(self, url):
        self.stop()
        self.media = self.instance.media_new(url)
        self.player.set_media(self.media)
        self.player.play()

        self.is_playing = True
        self.is_paused = False

        # Wait until VLC reports it's playing
        max_tries = 30
        for _ in range(max_tries):
            state = self.player.get_state()
            if state == vlc.State.Playing:
                break
            time.sleep(0.1)

        self._running = True
        self._update_thread = threading.Thread(target=self._update_position, daemon=True)
        self._update_thread.start()
        
    def _update_position(self):
        """Thread that updates the position and checks for track end."""
        while self._running and self.is_playing:
            if not self.is_paused and self.player.is_playing():
                # Get current position and duration in milliseconds
                position_ms = self.player.get_time()
                duration_ms = self.player.get_length()
                
                # Convert to seconds for the callback
                position_sec = position_ms / 1000 if position_ms >= 0 else 0
                duration_sec = duration_ms / 1000 if duration_ms > 0 else 0
                
                # Call the position callback if set
                if self._position_callback and duration_sec > 0:
                    try:
                        self._position_callback(position_sec, duration_sec)
                    except Exception as e:
                        print(f"Error in position callback: {e}")
                
                # Check if track has ended
                state = self.player.get_state()
                if state == vlc.State.Ended or (duration_ms > 0 and position_ms >= duration_ms - 500):
                    if self._on_end_callback:
                        try:
                            self._on_end_callback()
                        except Exception as e:
                            print(f"Error in end callback: {e}")
                    break
            
            # Sleep briefly to avoid consuming too much CPU
            time.sleep(0.25)
        
    def set_position_callback(self, callback):
        """Set the callback function for position updates."""
        self._position_callback = callback
        
    def set_on_end_callback(self, callback):
        """Set the callback function for end of playback."""
        self._on_end_callback = callback
        
    def pause(self):
        """Pause playback."""
        if self.is_playing and not self.is_paused:
            self.player.pause()
            self.is_paused = True
            
    def resume(self):
        """Resume playback after pause."""
        if self.is_playing and self.is_paused:
            self.player.play()
            self.is_paused = False
            
    def toggle_pause(self):
        """Toggle between play and pause."""
        if self.is_paused:
            self.resume()
        else:
            self.pause()
            
    def stop(self):
        """Stop playback completely."""
        # Signal thread to stop
        self._running = False
        
        # Stop the player
        if self.is_playing:
            self.player.stop()
            self.is_playing = False
            self.is_paused = False
            
        # Wait for thread to terminate
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)
            
    def get_current_time(self):
        """Get the current playback position in seconds."""
        if not self.is_playing:
            return 0
        time_ms = self.player.get_time()
        return time_ms / 1000 if time_ms >= 0 else 0
    
    def get_duration(self):
        """Get the total duration in seconds."""
        if not self.is_playing:
            return 0
        length_ms = self.player.get_length()
        return length_ms / 1000 if length_ms > 0 else 0
        
    def is_currently_playing(self):
        """Check if player is currently playing (not paused or stopped)."""
        return self.is_playing and not self.is_paused

async def on_input_submitted(self, event: Input.Submitted) -> None:
    # Do nothing on enter
    pass

async def on_timer(self):
    """Periodic update for syncing lyrics with playback."""
    if hasattr(self, "lyrics_display") and self.lyrics_display:
        pos = self.get_current_playback_position()
        self.lyrics_display.update_position(pos)

def get_current_playback_position(self):
    return self.player.get_current_time()

def search_dab(query: str, search_type: str = "track", offset: int = 0):
    base_url = get_base_url()
    params = {"q": query, "offset": offset, "type": search_type}
    full_url = f"{base_url}/search?{urlencode(params)}"
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[red]Request failed[/red]: {e}")
    return None

def fetch_all_results(query, search_type):
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
    base_url = get_base_url()
    url = f"{base_url}/stream?trackId={track_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("url")
    except Exception as e:
        print(f"[red]Failed to get streaming URL[/red]: {e}")
    return None

def get_track_detail(track_id):
    base_url = get_base_url()
    url = f"{base_url}/track/{track_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[red]Failed to get track details[/red]: {e}")
    return None

class LyricsDisplay(Widget):
    def compose(self):
        self.scroll = ScrollableContainer(id="lyrics_display")
        yield self.scroll

    def on_mount(self):
        self.styles.height = 20
        self.has_lyrics = False
        self.lyrics_lines = []
        self.line_widgets = []
        self.current_line_index = -1

        self.scroll.mount(Static("Waiting for lyrics...", id="lyrics_placeholder"))

        try:
            from lrclib import LrcLibAPI
            self.api = LrcLibAPI(user_agent="music-player/1.0.0")
            self.lrclib_available = True
        except ImportError:
            print("lrclib package not found. Please install it with: pip install lrclibapi")
            self.lrclib_available = False

    def parse_lyrics(self, raw_lyrics: str):
        self.lyrics_lines = []
        for line in raw_lyrics.splitlines():
            match = re.match(r"\[([0-9]+):([0-9]+\.[0-9]+)\](.*)", line)
            if match:
                min_str, sec_str, text = match.groups()
                timestamp = int(min_str) * 60 + float(sec_str)
                self.lyrics_lines.append((timestamp, text.strip()))
        
        if not self.lyrics_lines:
            self.has_lyrics = False
        else:
            self.lyrics_lines.sort()
            self.has_lyrics = True

    def update_content(self):
        self.scroll.remove_children()
        self.line_widgets = []

        if self.has_lyrics and self.lyrics_lines:
            for _, text in self.lyrics_lines:
                widget = Static(text)
                self.scroll.mount(widget)
                self.line_widgets.append(widget)
            self.scroll.refresh()
        else:
            self.scroll.mount(Static("Lyrics not found."))
            self.scroll.refresh()

    def fetch_lyrics(self, artist, title, album=None, duration=None):
        if not artist or not title:
            self.has_lyrics = False
            self.lyrics_lines = []
            self.update_content()
            return False

        if not self.lrclib_available:
            self.scroll.remove_children()
            self.scroll.mount(Static("lrclib not available."))
            self.scroll.refresh()
            return False

        try:
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Fetching lyrics for '{title}' by '{artist}'..."))
            self.scroll.refresh()

            if album or duration:
                lyrics_result = self.api.get_lyrics(track_name=title, artist_name=artist, album_name=album, duration=duration)
                raw_lyrics = lyrics_result.synced_lyrics or lyrics_result.plain_lyrics
            else:
                results = self.api.search_lyrics(track_name=title, artist_name=artist)
                if results:
                    lyrics_result = self.api.get_lyrics_by_id(results[0].id)
                    raw_lyrics = lyrics_result.synced_lyrics or lyrics_result.plain_lyrics
                else:
                    raw_lyrics = None

            if raw_lyrics:
                self.parse_lyrics(raw_lyrics)
                self.update_content()
                self.current_line_index = -1
                return True
            else:
                self.scroll.remove_children()
                self.scroll.mount(Static("No lyrics found"))
                self.scroll.refresh()

        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error fetching lyrics: {str(e)}"))
            self.scroll.refresh()

        self.has_lyrics = False
        self.update_content()
        return False

    async def highlight_line(self, index: int):
        """Highlight the current line and scroll to it, adding an arrow to the current line."""
        if not self.line_widgets or len(self.line_widgets) != len(self.lyrics_lines):
            print("Line widgets and lyrics lines don't match!")
            return
        
        # Calculate visible range to optimize updates (show past and upcoming lines)
        visible_range = 5  # Number of lines to show before and after current
        start_idx = max(0, index - visible_range)
        end_idx = min(len(self.line_widgets) - 1, index + visible_range)
            
        # Update only the visible lines to improve performance
        for i, widget in enumerate(self.line_widgets):
            if start_idx <= i <= end_idx:
                if i == index:
                    # Current line with arrow
                    widget.update(f"→ {self.lyrics_lines[i][1]}")
                    widget.styles.color = "yellow"
                    widget.styles.bold = True
                elif i == index - 1:
                    # Previous line (dimmed)
                    widget.update(self.lyrics_lines[i][1])
                    widget.styles.color = "gray"
                    widget.styles.bold = False
                elif i == index + 1:
                    # Next line (slightly highlighted)
                    widget.update(self.lyrics_lines[i][1])
                    widget.styles.color = "white"
                    widget.styles.bold = False
                else:
                    # Regular line
                    widget.update(self.lyrics_lines[i][1])
                    widget.styles.color = None
                    widget.styles.bold = False
        
        # Make sure we refresh the display
        self.refresh()
        
        # Center the current line in view (with some lines above for context)
        if 0 <= index < len(self.line_widgets):
            center_offset = 2  # Show 2 lines above the current line when possible
            center_index = max(0, index - center_offset)
            self.scroll.scroll_to_widget(self.line_widgets[center_index], animate=False)

    def search_lyrics(self, query):
        """Search for lyrics using a general query."""
        if not self.lrclib_available:
            self.scroll.remove_children()
            self.scroll.mount(Static("lrclib library not available. Please install it."))
            self.scroll.refresh()
            return None
            
        try:
            # Show status while searching
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Searching for lyrics: '{query}'..."))
            self.scroll.refresh()
            
            # Search for lyrics
            results = self.api.search_lyrics(track_name=query)
            
            if results:
                # Format results for display
                self.scroll.remove_children()
                self.scroll.mount(Static(f"Found {len(results)} results for '{query}':"))
                
                # Display up to 10 results
                for i, result in enumerate(results[:10]):
                    info = f"{i+1}. {result.artist_name} - {result.track_name}"
                    if result.album_name:
                        info += f" ({result.album_name})"
                    self.scroll.mount(Static(info))
                
                self.scroll.refresh()
                return results
            else:
                self.scroll.remove_children()
                self.scroll.mount(Static(f"No results found for '{query}'"))
                self.scroll.refresh()
                return None
                
        except Exception as e:
            print(f"Failed to search lyrics: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error searching lyrics: {str(e)}"))
            self.scroll.refresh()
            return None
            
    def get_lyrics_by_result(self, result_index, results):
        """Get lyrics from a specific search result."""
        if not results or result_index >= len(results):
            return False
            
        try:
            # Show status while fetching
            self.scroll.remove_children()
            self.scroll.mount(Static("Fetching lyrics from selected result..."))
            self.scroll.refresh()
            
            # Get lyrics by ID
            lyrics_result = self.api.get_lyrics_by_id(results[result_index].id)
            raw_lyrics = lyrics_result.synced_lyrics or lyrics_result.plain_lyrics
            
            if raw_lyrics:
                self.parse_lyrics(raw_lyrics)
                self.update_content()
                self.current_line_index = -1
                return True
            else:
                self.scroll.remove_children()
                self.scroll.mount(Static("No lyrics found in the selected result"))
                self.scroll.refresh()
                return False
                
        except Exception as e:
            print(f"Failed to fetch lyrics from result: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error fetching lyrics: {str(e)}"))
            self.scroll.refresh()
            return False
    
    def update_position(self, position_seconds: float):
        """Highlight the current lyrics line based on the song's progress."""
        if not self.has_lyrics or not self.lyrics_lines:
            return

        # Find the last lyric line that should be shown for the current time
        index = -1
        for i, (timestamp, _) in enumerate(self.lyrics_lines):
            if position_seconds >= timestamp:
                index = i
            else:
                break

        # Avoid unnecessary updates
        if index == self.current_line_index or index == -1:
            return

        self.current_line_index = index

        # Update styles for all lines
        for i, widget in enumerate(self.line_widgets):
            if i == index:
                widget.update(f"→ {self.lyrics_lines[i][1]}")
                widget.styles.color = "yellow"
                widget.styles.bold = True
            else:
                widget.update(self.lyrics_lines[i][1])
                widget.styles.color = None
                widget.styles.bold = False

        # Scroll to the current line
        self.scroll.scroll_to_widget(self.line_widgets[index], animate=False)


class Results(App):
    CSS = """
    /* Make sure our timestamp display stays visible at the bottom */
    #progress_container {
        dock: bottom;
        height: 2;  /* Reduced height since we're removing the visual bar */
        margin: 0;
        padding: 0;
        background: $surface;
        border-top: solid $accent;
    }
    
    #progress_bar_content {
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
        background: $surface;
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
    
    /* Style for the controls hint */
    #controls_hint {
        text-align: center;
        color: $text-muted;
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
        ("l", "toggle_lyrics", "Show/Hide Lyrics")
        #("r", "toggle_repeat", "Repeat Mode")
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
        
    def compose(self) -> ComposeResult:
        yield Header(f"DAB Terminal - Search: '{self.query}'")

        # Main content
        with Vertical():
            self.search_input = Input(placeholder="Search for a new track...", id="search_input")
            self.search_input.styles.display = "none"
            yield self.search_input

            self.now_playing = Static("Not Playing", id="now_playing")
            yield self.now_playing

            self.lyrics_display = LyricsDisplay(id="lyrics_display")
            yield self.lyrics_display
            self.lyrics_display.styles.display = "none"

            self.table = DataTable(id="results_table")
            yield self.table

            self.progress_visual = Static("▕░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▏")
            yield self.progress_visual

            yield Static(id="progress_bar")

            # self.progress_bar_content = Static("0:00 / 0:00", id="progress-time")
            # yield self.progress_bar_content

            self.pagination = Static(id="pagination")
            yield self.pagination

            self.info = Static("", id="info")
            yield self.info

        # Simple timestamp container instead of progress bar
        with Container(id="progress_container"):
            yield Static("0:00 / 0:00 (Not Playing)", id="progress_bar_content")  # Time info
            yield Static("Press SPACE to play/pause | ESC to stop", id="controls_hint")  # Controls hint

        # Footer must be after the progress bar
        yield Footer()

    def on_mount(self):
        """Set up the UI when the app is mounted."""
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.table.show_cursor = True
        self.table.focus()
        self.update_page()  # Assuming this method exists
        
        # Get references to progress elements
        self.progress_bar_content = self.query_one("#progress_bar_content")
        self.controls_hint = self.query_one("#controls_hint")
        
        # Configure initial styles
        self.progress_bar_content.styles.color = "ansi_bright_white"  # Make text more visible
        
        # Set up player callbacks
        self.player.set_position_callback(self.update_progress)
        self.player.set_on_end_callback(self.on_track_end)
        
        # Set initial progress display
        # self.progress_bar_content.update("0:00 / 0:00 (Not Playing)")
        
        # Configure lyrics display
        self.lyrics_display = self.query_one("#lyrics_display")
        self.lyrics_display.styles.display = "none"
        
        # Start a regular UI update timer to ensure progress bar updates even if callback is missed
        self.set_interval(0.5, self.check_progress_updates)
        
    def check_progress_updates(self):
        """Regular timer callback to ensure progress bar updates."""
        if self.player.is_currently_playing():
            position = self.player.get_current_time()
            duration = self.player.get_duration()
            if duration > 0:
                self._update_progress_ui(position, duration)
    
    def play_track(self, track_info):
        """Play a track and update the UI accordingly."""
        if not track_info:
            return
            
        # Store current track info
        self.currently_playing = track_info
        self.is_paused = False
        
        # Update UI to show what's playing
        self.now_playing.update(f"Now Playing: {track_info['title']} - {track_info['artist']}")
        
        # Reset progress bar with enhanced UI
        self.progress_bar_content.remove_class("paused")
        self.progress_bar_content.add_class("playing")
        
        self.progress_bar_content.update("0:00 / 0:00 (Loading...)")
        
        # Start playback using the URL from track_info
        stream_url = track_info.get('stream_url')
        if stream_url:
            self.player.play(stream_url)
            # Log that playback has started
            print(f"Starting playback of {track_info['title']}")
    
    def update_progress(self, position, duration):
        self._update_progress_ui(position, duration)

    def action_toggle_play(self):
        """Handle play/pause action."""
        if not self.currently_playing:
            # Nothing is playing, so try to play the selected track
            selected_row = self.table.cursor_row
            if selected_row >= 0 and selected_row < len(self.displayed_results):
                self.play_track(self.displayed_results[selected_row])
        else:
            # Toggle pause/resume on currently playing track
            if self.is_paused:
                self.player.resume()
                self.is_paused = False
                self.progress_bar_content.remove_class("paused")
                self.progress_bar_content.add_class("playing")
                
                # Update the content to show "Playing" status
                current_text = self.progress_bar_content.renderable
                if isinstance(current_text, str) and "(Paused)" in current_text:
                    new_text = current_text.replace("(Paused)", "(Playing)")
                    self.progress_bar_content.update(new_text)
            else:
                self.player.pause()
                self.is_paused = True
                self.progress_bar_content.remove_class("playing")
                self.progress_bar_content.add_class("paused")
                
                # Update the content to show "Paused" status
                current_text = self.progress_bar_content.renderable
                if isinstance(current_text, str) and "(Playing)" in current_text:
                    new_text = current_text.replace("(Playing)", "(Paused)")
                    self.progress_bar_content.update(new_text)
                elif isinstance(current_text, str) and not "(Paused)" in current_text:
                    # If there's no status indicator yet
                    self.progress_bar_content.update(f"{current_text} (Paused)")
    
    def action_stop_playback(self):
        """Stop the current playback."""
        self.player.stop()
        self.currently_playing = None
        self.is_paused = False
        self.now_playing.update("Not Playing")
        
        # Reset progress display styling
        self.progress_bar_content.remove_class("playing")
        self.progress_bar_content.remove_class("paused")
        
        # Reset progress display text
        self.progress_bar_content.update("0:00 / 0:00 (Not Playing)")
        
        # Hide lyrics display if showing
        if self.lyrics_display and self.lyrics_display.styles.display != "none":
            self.lyrics_display.styles.display = "none"
    
    def get_current_playback_position(self):
        """Return current playback time in seconds from player."""
        return self.player.get_current_time()

    def update_progress_bar(self, position: float, duration: float):
        """Update a simple textual progress bar."""
        bar_width = 40  # width of the progress bar
        if duration <= 0:
            progress_text = "0:00 / 0:00"
            bar = "▕" + "░" * bar_width + "▏"
        else:
            percent = min(position / duration, 1.0)
            filled = int(bar_width * percent)
            empty = bar_width - filled
            minutes_pos, seconds_pos = divmod(int(position), 60)
            minutes_dur, seconds_dur = divmod(int(duration), 60)
            time_text = f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d}"
            bar = f"▕{'█' * filled}{'░' * empty}▏"
            progress_text = f"{bar} {time_text}"

        self.query_one("#progress_bar", Static).update(progress_text)

    def _update_progress_ui(self, position, duration):
        """Updates the timestamp display on the main thread."""
        if not self.progress_bar_content or duration <= 0:
            return
        
        # Calculate the current and total time in minutes and seconds
        minutes_pos = int(position // 60)
        seconds_pos = int(position % 60)
        minutes_dur = int(duration // 60)
        seconds_dur = int(duration % 60)

        # Format timestamp with progress percentage
        percent = min(position / duration * 100, 100)  # Percentage played
        
        # Determine playback status text
        status = "(Paused)" if self.is_paused else "(Playing)"
        if not self.currently_playing:
            status = "(Not Playing)"
            
        # Create a clear timestamp with percentage
        time_text = f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d} ({percent:.1f}%) {status}"
        
        # Update the component
        self.progress_bar_content.update(time_text)
        
        # Update lyrics position if visible
        if hasattr(self, 'lyrics_display') and self.lyrics_display and self.lyrics_display.styles.display != "none":
            self.lyrics_display.update_position(position)

    def _update_progress_ui(self, position, duration):
        """Updates the UI components on the main thread."""
        if not self.progress_bar_content or duration <= 0:
            return
        
        bar_width = 80
        percent = min(position / duration, 1.0)
        filled = int(bar_width * percent)
        empty = bar_width - filled
        minutes_pos, seconds_pos = divmod(int(position), 60)
        minutes_dur, seconds_dur = divmod(int(duration), 60)
        time_text = f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d}"
        bar = f"▕{'█' * filled}{'░' * empty}▏"
        progress_text = f"{bar} {time_text}"
        
        # Determine playback status text
        status = "(Paused)" if self.is_paused else "(Playing)"
        if not self.currently_playing:
            status = "(Not Playing)"
            
        # Update the time text and visual bar separately
        time_text = f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d} {status}"
        
        # Update the components
        self.progress_visual.update(bar)
        self.query_one("#progress_bar", Static).update(progress_text)
        
        # Update lyrics position if visible
        if hasattr(self, 'lyrics_display') and self.lyrics_display and self.lyrics_display.styles.display != "none":
            self.lyrics_display.update_position(position)

    def on_track_end(self):
        """Handle what happens when a track finishes playing."""
        # Need to call from thread to update UI safely
        self.call_from_thread(self._handle_track_end)

    def _handle_track_end(self):
        """Handle track end in the main thread."""
        # Reset the timestamp display with clear end state
        self.progress_bar_content.update("0:00 / 0:00 (Finished)")
        
        # Use existing logic for repeat functionality
        if self.repeat and self.currently_playing:
            self.play_track(self.currently_playing)
        else:
            self.currently_playing = None
            self.now_playing.update("Not Playing")

    def update_page(self):
        self.table.clear(columns=True)
        self.table.add_columns("Title", "Artist", "Album", "Duration")
        start_idx = self.current_page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(self.results))
        for item in self.results[start_idx:end_idx]:
            duration = item.get("duration", 0)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
            self.table.add_row(item.get("title", "Unknown"), item.get("artist", "Unknown"), item.get("albumTitle", "Unknown"), duration_str)
        pagination_text = f"Page {self.current_page + 1}/{self.total_pages} | Items {start_idx + 1}-{end_idx} of {len(self.results)}"
        self.pagination.update(pagination_text)
        self.showing_info = False
        self.info.styles.height = 1

    def action_next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()

    def action_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def play_track(self, track):
        track_id = track.get("id")
        if not track_id:
            self.notify("No track ID found", title="Play Error")
            return
        self.stop_playback()
        stream_url = get_streaming_url(track_id)
        if not stream_url:
            self.notify("No streaming URL found", title="Play Error")
            return
        self.player.play(stream_url)
        self.currently_playing = track
        self.is_paused = False
        repeat_status = "[Repeat ON]" if self.repeat else ""
        self.now_playing.update(f"Now Playing: {track.get('title')} - {track.get('artist')} {repeat_status}")
        
        # Fetch lyrics if the lyrics display is visible
        if self.lyrics_display.styles.display != "none":
            artist = track.get("artist", "")
            title = track.get("title", "")
            self.lyrics_display.fetch_lyrics(artist, title)
        
        self.notify(f"Playing: {track.get('title')}", title="Now Playing")

    def action_play_selected(self):
        row_index = self.table.cursor_row
        if 0 <= row_index < min(ITEMS_PER_PAGE, len(self.results) - (self.current_page * ITEMS_PER_PAGE)):
            actual_index = (self.current_page * ITEMS_PER_PAGE) + row_index
            self.play_track(self.results[actual_index])

    def toggle_play(self):
        if not self.currently_playing:
            self.action_play_selected()
        else:
            if self.is_paused:
                self.player.resume()
                self.is_paused = False
                self.notify("Playback resumed", title="Playback")
            else:
                self.player.pause()
                self.is_paused = True
                self.notify("Playback paused", title="Playback")

    def stop_playback(self):
        if self.currently_playing:
            self.player.stop()
            self.currently_playing = None
            self.is_paused = False
            self.now_playing.update("Not Playing")
            self.progress_bar_content.update("")
            self.notify("Playback stopped", title="Playback")

    def action_fast_forward(self):
        if self.player.is_playing:
            current_time = self.player.player.get_time()
            new_time = current_time + 5000  # 5 seconds
            duration = self.player.player.get_length()
            if new_time < duration:
                self.player.player.set_time(new_time)
                self.notify("Fast forwarded 5 seconds", title="Seek")
    
    def action_rewind(self):
        if self.player.is_playing:
            current_time = self.player.player.get_time()
            new_time = max(0, current_time - 5000)
            self.player.player.set_time(new_time)
            self.notify("Rewound 5 seconds", title="Seek")
    
    def action_toggle_repeat(self):
        self.repeat = not self.repeat
        repeat_status = "ON" if self.repeat else "OFF"
        self.notify(f"Repeat mode: {repeat_status}", title="Repeat Mode")
        if self.currently_playing:
            self.now_playing.update(f"Now Playing: {self.currently_playing.get('title')} - {self.currently_playing.get('artist')} [Repeat {repeat_status}]")
    
    def action_submit_search(self):
        query = self.search_input.value.strip()
        if not query:
            self.search_input.styles.display = "none"
            self.set_focus(self.table)
            return

        self.stop_playback()
        self.search_input.styles.display = "none"
        self.set_focus(self.table)
        self.query_focus = False
        self.query = query

        def do_search():
            new_results = fetch_all_results(query, self.search_type)
            if not new_results:
                self.call_from_thread(lambda: self.notify("No results found", title="Search"))
                return

            def update_ui():
                self.results = new_results
                self.current_page = 0
                self.total_pages = ceil(len(self.results) / ITEMS_PER_PAGE)
                self.update_page()
                self.info.update("")
                self.info.styles.height = 1
                self.showing_info = False
                self.set_title(f"DAB Terminal - Search: '{self.query}'")

            self.call_from_thread(update_ui)

        threading.Thread(target=do_search, daemon=True).start()

    def on_track_end(self):
        if self.repeat and self.currently_playing:
            self.call_from_thread(lambda: self.play_track(self.currently_playing))
    
    def format_track_info(self, track):
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
        row_index = self.table.cursor_row
        if 0 <= row_index < min(ITEMS_PER_PAGE, len(self.results) - (self.current_page * ITEMS_PER_PAGE)):
            actual_index = (self.current_page * ITEMS_PER_PAGE) + row_index
            track = self.results[actual_index]
            self.showing_info = not self.showing_info
            if self.showing_info:
                track_info_table = self.format_track_info(track)
                track_info_panel = Panel(track_info_table, title=f"Track Info: {track.get('title', 'Unknown')}", border_style="green")
                self.info.update(track_info_panel)
                self.info.styles.height = "auto"
            else:
                self.info.update("")  # Clear the panel content
                self.info.styles.height = 1

    def action_search(self):
        if self.search_input.styles.display == "none":
            self.search_input.styles.display = "block"
            self.set_focus(self.search_input)
            self.query_focus = True
        else:
            self.search_input.styles.display = "none"
            self.set_focus(self.table)
            self.query_focus = False
    
    def setup_lyrics_display(self):
        """Set up the lyrics display widget."""
        self.lyrics_display = LyricsDisplay(id="lyrics_display")
        self.lyrics_display.styles.display = "none"  # Hide initially
        return self.lyrics_display

    def action_toggle_lyrics(self):
        """Toggle the visibility of lyrics display."""
        if not hasattr(self, 'lyrics_display') or self.lyrics_display is None:
            self.lyrics_display = self.query_one("#lyrics_display", Static)
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

                self.lyrics_display.visible = True
                self.notify("Showing lyrics", title="Lyrics")
            else:
                self.notify("No track currently playing", title="Lyrics")
        else:
            self.lyrics_display.styles.display = "none"
            self.notify("Hiding lyrics", title="Lyrics")

    def action_toggle_play(self):
        self.toggle_play()

    def action_stop_playback(self):
        self.stop_playback()

    def on_unmount(self):
        self.player.stop()

    def action_quit(self):
        self.exit()

def main():
    while True:
        query = Prompt.ask("[bold]Enter your search query[/bold]")
        search_type = Prompt.ask("[bold]Search for[/bold]", choices=["track", "album(not supported yet)"])
        if search_type == "album":
            print("[yellow]Only track browsing is supported for selection. Defaulting to 'track'.[/yellow]")
            search_type = "track"
        all_results = fetch_all_results(query, search_type)
        if not all_results:
            print("[red]No results found. Try another search.[/red]")
            continue
        app = Results(all_results, search_type, query)
        exit_code = app.run()
        continue_search = Prompt.ask("[bold]Sure you wanna exit?[/bold]", choices=["y", "n"])
        if continue_search.lower() != "n":
            break

if __name__ == "__main__":
    main()
