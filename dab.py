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
        self.instance = vlc.Instance('--no-xlib')
        self.player = self.instance.media_player_new()
        self.media = None
        self.is_playing = False
        self.duration = 0
        self.position = 0
        self._position_thread = None
        self._position_callback = None
        self._on_end_callback = None
        self._end_thread = None

    def play(self, url):
        self.stop()
        self.media = self.instance.media_new(url)
        self.player.set_media(self.media)
        self.player.play()
        self.is_playing = True
        time.sleep(0.5)
        self.duration = self.player.get_length() / 1000
        self._start_position_tracking()
        self._start_end_detection()

    def _start_position_tracking(self):
        if self._position_thread and self._position_thread.is_alive():
            return
        def update_position():
            while self.is_playing:
                if self.player.is_playing():
                    self.position = self.player.get_time() / 1000
                    if self._position_callback:
                        self._position_callback(self.position, self.duration)
                time.sleep(0.5)
        self._position_thread = threading.Thread(target=update_position, daemon=True)
        self._position_thread.start()
    
    def _start_end_detection(self):
        if self._end_thread and self._end_thread.is_alive():
            return
        def check_end():
            while self.is_playing:
                if self.duration > 0 and self.player.get_time() >= self.player.get_length() - 500:
                    if self._on_end_callback:
                        self._on_end_callback()
                    break
                time.sleep(0.5)
        self._end_thread = threading.Thread(target=check_end, daemon=True)
        self._end_thread.start()

    def set_position_callback(self, callback):
        self._position_callback = callback
    
    def set_on_end_callback(self, callback):
        self._on_end_callback = callback

    def pause(self):
        if self.is_playing:
            self.player.pause()

    def resume(self):
        if self.is_playing:
            self.player.play()

    def stop(self):
        if self.is_playing:
            self.player.stop()
            self.is_playing = False
            self.position = 0
            self.duration = 0

    def get_current_time(self):
        return self.position

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
        """Compose method to define widget structure."""
        self.scroll = ScrollableContainer(id="lyrics_display")
        self.lyrics_static = Static("Waiting for lyrics...", id="lyrics_text")
        yield self.scroll

    def on_mount(self):
        """Setup initial state and properties when widget is mounted."""
        self.styles.height = "80%"
        self.lyrics_static.update("Waiting for lyrics...")
        self.has_lyrics = False
        self.lyrics_data = {}
        self.lyrics_lines = []
        self.current_line_index = 0
        self.lyric_task = None

        # Mount the Static widget after the ScrollableContainer is mounted
        self.scroll.mount(self.lyrics_static)

    def stop_lyrics_loop(self):
        """Stop the lyrics loop if it's running."""
        if self.lyric_task:
            self.lyric_task.cancel()
            self.lyric_task = None

    def parse_lyrics(self, raw_lyrics: str):
        """Parse LRC format to a list of (time, text) tuples."""
        self.lyrics_lines = []
        for line in raw_lyrics.splitlines():
            # Match timestamp and lyrics in the LRC format
            match = re.match(r"\[([0-9]+:[0-9]+\.[0-9]+)\](.*)", line)
            if match:
                time_str, text = match.groups()
                minutes, seconds = map(float, time_str.split(":"))
                timestamp = minutes * 60 + seconds
                self.lyrics_lines.append((timestamp, text.strip()))
        self.lyrics_lines.sort()  # Sort by timestamp

    def update_content(self):
        """Update lyrics display content."""
        if self.has_lyrics:
            # Update the static widget with lyrics content
            content = "\n".join([line for _, line in self.lyrics_lines])
        else:
            content = "Lyrics not found."
        self.lyrics_static.update(content)

    def fetch_lyrics(self, artist, title):
        """Fetch lyrics from the API using the provided function."""
        if not artist or not title:
            self.has_lyrics = False
            self.lyrics_data = {}
            self.lyrics_lines = []
            self.update_content()
            return False

        base_url = get_base_url()  # Using the existing function from your code
        url = f"{base_url}/lyrics?artist={requests.utils.quote(artist)}&title={requests.utils.quote(title)}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data and "lyrics" in data and data["lyrics"]:
                    self.lyrics_data = data
                    self.parse_lyrics(data["lyrics"])
                    self.has_lyrics = True
                    self.current_line_index = 0
                    self.update_content()
                    return True
                else:
                    self.has_lyrics = False
                    self.update_content()
                    return False
            else:
                self.has_lyrics = False
                self.update_content()
                return False
        except Exception as e:
            print(f"Failed to fetch lyrics: {e}")
            self.has_lyrics = False
            self.update_content()
            return False

    def _clean_lrc(self, lrc_text):
        """Remove timestamps like [00:12.34] from LRC lines."""
        return re.sub(r"\[\d+:\d+\.\d+\]", "", lrc_text).strip()
        
class Results(App):
    CSS = """
    #progress_bar_content {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        width: 100%;
        text-align: center;
        padding-bottom: 0;
        margin-bottom: 1;
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
    #("h", "fast_forward", "Forward"),
    #("g", "rewind", "Rewind"),
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
        # Initialize lyrics_display as None
        self.lyrics_display = None

    def compose(self) -> ComposeResult:
        yield Header(f"DAB Terminal - Search: '{self.query}'")

        with Vertical():
            self.search_input = Input(placeholder="Search for a new track...", id="search_input")
            self.search_input.styles.display = "none"
            yield self.search_input

            self.now_playing = Static("Not Playing", id="now_playing")
            yield self.now_playing

            self.lyrics_display = LyricsDisplay(id="lyrics_display")
            yield self.lyrics_display  # Scrollable container with lyrics
            self.lyrics_display.styles.display = "none"  # Hide initially

            self.table = DataTable(id="results_table")
            yield self.table

            self.pagination = Static(id="pagination")
            yield self.pagination

            self.info = Static("", id="info")
            yield self.info

        self.progress_bar_content = Static("", id="progress_bar_content")
        yield self.progress_bar_content

        yield Footer(id="footer")

    def on_mount(self):
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.table.show_cursor = True
        self.table.focus()
        self.update_page()
        self.player.set_position_callback(self.update_progress)
        self.player.set_on_end_callback(self.on_track_end)
        self.query_focus = False

        self.lyrics_display = self.query_one("#lyrics_display", LyricsDisplay)
        self.lyrics_display.styles.display = "none"
        
    def get_current_playback_position(self):
        """Return current playback time in seconds from player."""
        return self.player.get_current_time()

    def update_progress(self, position, duration):
        """Updates the progress bar display as the song plays and updates lyrics."""
        if duration > 0:
            # Calculate the percentage of the song played
            percent = (position / duration)
            bar_width = 30  # Width of the progress bar
            filled = int(percent * bar_width)
            empty = bar_width - filled

            # Calculate the current and total time in minutes and seconds
            minutes_pos = int(position // 60)
            seconds_pos = int(position % 60)
            minutes_dur = int(duration // 60)
            seconds_dur = int(duration % 60)

            # Create a text-based progress bar with clear styling
            bar = "▕" + "█" * filled + "░" * empty + "▏"
            text = f"{bar} {minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d}"

            # Update the progress bar display
            self.progress_bar_content.update(text)
            
            # Update lyrics position if visible
            if self.lyrics_display.styles.display != "none":
                self.lyrics_display.update_position(position)
    
    def on_track_end(self):
        """Handles what happens when the track ends."""
        self.progress_bar_content.update("Playback finished")

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
                self.lyrics_display.fetch_lyrics(artist, title)

                # Start background loop
                if hasattr(self, 'lyrics_display') and self.lyrics_display:
                    self.lyrics_display.visible = True
                self.notify("Showing lyrics", title="Lyrics")
            else:
                self.notify("No track currently playing", title="Lyrics")
        else:
            self.lyrics_display.stop_lyrics_loop()
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
