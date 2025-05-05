import requests
import json
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from urllib.parse import urlencode
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Label
from textual.containers import Vertical
from textual.binding import Binding
from textual.widget import Widget
from math import ceil
import vlc
import threading
import time
from rich.text import Text

# Constants
BASE_URL = "https://dab.yeet.su/api"
ITEMS_PER_PAGE = 10
console = Console()

class AudioPlayer:
    """Handles audio playback functionality"""
    
    def __init__(self):
        self.instance = vlc.Instance('--no-xlib')
        self.player = self.instance.media_player_new()
        self.media = None
        self.is_playing = False
        self.duration = 0
        self.position = 0
        self._position_thread = None
        self._position_callback = None
        
    def play(self, url):
        """Start playing audio from URL"""
        # Stop any current playback
        self.stop()
        
        # Create new media and play
        self.media = self.instance.media_new(url)
        self.player.set_media(self.media)
        self.player.play()
        self.is_playing = True
        
        # Wait for media to load
        time.sleep(0.5)
        self.duration = self.player.get_length() / 1000  # convert to seconds
        
        # Start position tracking thread
        self._start_position_tracking()
        
    def _start_position_tracking(self):
        """Start thread to track playback position"""
        if self._position_thread and self._position_thread.is_alive():
            return
            
        def update_position():
            while self.is_playing:
                if self.player.is_playing():
                    self.position = self.player.get_time() / 1000  # convert to seconds
                    if self._position_callback:
                        self._position_callback(self.position, self.duration)
                time.sleep(0.5)
        
        self._position_thread = threading.Thread(target=update_position, daemon=True)
        self._position_thread.start()
        
    def set_position_callback(self, callback):
        """Set callback function for position updates"""
        self._position_callback = callback
        
    def pause(self):
        """Pause playback"""
        if self.is_playing:
            self.player.pause()
    
    def resume(self):
        """Resume playback"""
        if self.is_playing:
            self.player.play()
    
    def stop(self):
        """Stop playback"""
        if self.is_playing:  # Only attempt to stop if we're actually playing
            self.player.stop()
            self.is_playing = False
            self.position = 0
            self.duration = 0


def search_dab(query: str, search_type: str = "track", offset: int = 0):
    """Search for tracks or albums on dab.yeet.su"""
    params = {
        "q": query,
        "offset": offset,
        "type": search_type
    }
    full_url = f"{BASE_URL}/search?{urlencode(params)}"
    
    # print(f"[bold blue]DEBUG:[/bold blue] Making request to: [cyan]{full_url}[/cyan]")
    
    try:
        response = requests.get(full_url)
        # print(f"[bold blue]DEBUG:[/bold blue] Status Code: [yellow]{response.status_code}[/yellow]")
        
        if response.status_code == 200:
            data = response.json()
            # print(f"[bold blue]DEBUG:[/bold blue] JSON keys in response: {list(data.keys())}")
            return data
        else:
            # print(f"[red]Error: HTTP {response.status_code}[/red]")
            return None
    except Exception as e:
        print(f"[red]Request failed[/red]: {e}")
        return None

def fetch_all_results(query, search_type):
    """Fetch all available results by paginating through the API"""
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
    """Get streaming URL for a track"""
    url = f"{BASE_URL}/stream?trackId={track_id}"
    # print(f"[bold blue]DEBUG:[/bold blue] Fetching streaming URL from: [cyan]{url}[/cyan]")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # print(f"[bold blue]DEBUG:[/bold blue] Streaming URL response: {data}")
            return data.get("url")
        else:
            print(f"[red]Error fetching streaming URL: HTTP {response.status_code}[/red]")
            return None
    except Exception as e:
        print(f"[red]Failed to get streaming URL[/red]: {e}")
        return None

def get_track_detail(track_id):
    """Get detailed information about a specific track"""
    url = f"{BASE_URL}/track/{track_id}"
    # print(f"[bold blue]DEBUG:[/bold blue] Fetching track details from: [cyan]{url}[/cyan]")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            track_data = response.json()
            return track_data
        else:
            print(f"[red]Error fetching track details: HTTP {response.status_code}[/red]")
            return None
    except Exception as e:
        print(f"[red]Failed to get track details[/red]: {e}")
        return None

class Results(App):
    """Main application for searching and viewing results"""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "show_info", "Show Info"),
        ("/", "search", "New Search"),
        ("n", "next_page", "Next Page"),
        ("p", "prev_page", "Prev Page"),
        ("space", "toggle_play", "Play/Pause"),
        ("escape", "stop_playback", "Stop")
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
        
        # Initialize audio player
        self.player = AudioPlayer()
        self.currently_playing = None
        self.is_paused = False
    
    def compose(self) -> ComposeResult:
        yield Header(f"DAB Terminal - Search: '{self.query}'")
        
        with Vertical():
            # Status bar for now playing and playback status
            self.now_playing = Static("Not Playing", id="now_playing")
            yield self.now_playing
            
            # Progress bar
            self.progress = Static("", id="progress_bar")
            yield self.progress
            
            # Results table
            self.table = DataTable(id="results_table")
            yield self.table
            
            # Pagination info
            self.pagination = Static(id="pagination")
            yield self.pagination
            
            # Info/help panel
            self.info = Static("", id="info")
            yield self.info
            
        yield Footer()
    
    def on_mount(self):
        """Set up the app when it mounts"""
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.table.show_cursor = True
        self.table.focus()

        self.update_page()
        self.player.set_position_callback(self.update_progress)
    
    def update_progress(self, position, duration):
        """Update the progress display"""
        if duration > 0:
            percent = (position / duration) * 100
            minutes_pos = int(position // 60)
            seconds_pos = int(position % 60)
            minutes_dur = int(duration // 60)
            seconds_dur = int(duration % 60)
            
            # Create a simple text-based progress bar
            progress_text = Text()
            progress_text.append(f"{minutes_pos}:{seconds_pos:02d} / {minutes_dur}:{seconds_dur:02d} ")
            
            # Simple ASCII progress bar
            bar_width = 40
            filled = int((percent / 100) * bar_width)
            progress_text.append("[")
            progress_text.append("=" * filled, style="green")
            progress_text.append(" " * (bar_width - filled))
            progress_text.append(f"] {percent:.1f}%")
            
            # Update the progress static widget
            self.progress.update(progress_text)
    
    def update_page(self):
        """Update the table with items for the current page"""
        self.table.clear(columns=True)
        self.table.add_columns("Title", "Artist", "Album", "Duration")
        
        # Calculate start and end indices for current page
        start_idx = self.current_page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(self.results))
        
        # Add rows for current page
        for item in self.results[start_idx:end_idx]:
            # Format duration as MM:SS
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
        
        # Update pagination info
        pagination_text = f"Page {self.current_page + 1}/{self.total_pages} | Items {start_idx + 1}-{end_idx} of {len(self.results)}"
        self.pagination.update(pagination_text)
        
        # Reset info panel
        self.showing_info = False
        # self.info.update("Use ↑/↓ to navigate. Press S for info. Space: play/pause. N/P: page.")
        self.info.styles.height = 1
    
    def action_next_page(self):
        """Go to the next page of results"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()
    
    def action_prev_page(self):
        """Go to the previous page of results"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()
    
    def play_track(self, track):
        """Play the selected track"""
        # Get track ID
        track_id = track.get("id")
        if not track_id:
            self.notify("No track ID found", title="Play Error")
            return
            
        # First stop any currently playing track
        self.stop_playback()
            
        # Get streaming URL
        stream_url = get_streaming_url(track_id)
        if not stream_url:
            self.notify("No streaming URL found", title="Play Error")
            return
            
        # Play the track
        # print(f"[bold green]Playing URL:[/bold green] {stream_url}")
        self.player.play(stream_url)
        self.currently_playing = track
        self.is_paused = False
        
        # Update now playing label
        self.now_playing.update(f"Now Playing: {track.get('title')} - {track.get('artist')}")
        self.notify(f"Playing: {track.get('title')}", title="Now Playing")
    
    def action_play_selected(self):
        """Play the currently selected track"""
        row_index = self.table.cursor_row
        if 0 <= row_index < min(ITEMS_PER_PAGE, len(self.results) - (self.current_page * ITEMS_PER_PAGE)):
            actual_index = (self.current_page * ITEMS_PER_PAGE) + row_index
            self.play_track(self.results[actual_index])
    
    def toggle_play(self):
        """Toggle play/pause state"""
        if not self.currently_playing:
            # Try to play selected track if no track is playing
            self.action_play_selected()
        else:
            # Toggle pause/resume if a track is already playing
            if self.is_paused:
                self.player.resume()
                self.is_paused = False
                self.notify("Playback resumed", title="Playback")
            else:
                self.player.pause()
                self.is_paused = True
                self.notify("Playback paused", title="Playback")
    
    def stop_playback(self):
        """Stop playback"""
        if self.currently_playing:  # Only try to stop if something is playing
            self.player.stop()
            self.currently_playing = None
            self.is_paused = False
            self.now_playing.update("Not Playing")
            self.progress.update("")
            self.notify("Playback stopped", title="Playback")
    
    def format_track_info(self, track):
        """Format track information for display"""
        # Get additional track details if available
        track_id = track.get("id")
        if track_id:
            detailed_info = get_track_detail(track_id)
            if detailed_info:
                track.update(detailed_info)
        
        # Format duration as MM:SS
        duration = track.get("duration", 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}:{seconds:02d}"
        
        # Create a table with track information
        table = Table(expand=True, box=None)
        table.add_column("Property")
        table.add_column("Value")
        
        table.add_row("Title", track.get("title", "Unknown"))
        table.add_row("Artist", track.get("artist", "Unknown"))
        table.add_row("Album", track.get("albumTitle", "Unknown"))
        table.add_row("Duration", duration_str)
        
        # Add additional details if available
        if "releaseDate" in track:
            table.add_row("Release Date", track.get("releaseDate", "Unknown"))
        
        if "genre" in track:
            table.add_row("Genre", track.get("genre", "Unknown"))
        
        if "bitrate" in track:
            table.add_row("Bitrate", f"{track.get('bitrate', 'Unknown')} kbps")
        
        if "format" in track:
            table.add_row("Format", track.get("format", "Unknown"))
        
        if "sampleRate" in track:
            table.add_row("Sample Rate", f"{track.get('sampleRate', 'Unknown')} Hz")
        
        if "label" in track:
            table.add_row("Label", track.get("label", "Unknown"))
        
        return table
    
    def action_show_info(self):
        """Show track information in a panel"""
        row_index = self.table.cursor_row
        if 0 <= row_index < min(ITEMS_PER_PAGE, len(self.results) - (self.current_page * ITEMS_PER_PAGE)):
            # Get the actual index in the full results list
            actual_index = (self.current_page * ITEMS_PER_PAGE) + row_index
            track = self.results[actual_index]
            
            # Toggle info panel visibility
            self.showing_info = not self.showing_info
            
            if self.showing_info:
                # Create and display track info
                track_info_table = self.format_track_info(track)
                track_info_panel = Panel(
                    track_info_table,
                    title=f"Track Info: {track.get('title', 'Unknown')}",
                    border_style="green"
                )
                
                # Update info static widget with the panel
                self.info.update(track_info_panel)
                self.info.styles.height = "auto"
            else:
                # Reset info panel
                # self.info.update("Use ↑/↓ to navigate. Press S for info. Space: play/pause. N/P: page.")
                self.info.styles.height = 1
    
    def action_search(self):
        """Start a new search"""
        # Simply exit - we'll handle new search in the main loop
        self.exit()
    
    def action_toggle_play(self):
        """Handle space key to toggle play/pause"""
        self.toggle_play()
    
    def action_stop_playback(self):
        """Handle escape key to stop playback"""
        self.stop_playback()
    
    def on_unmount(self):
        """Clean up when app unmounts"""
        self.player.stop()
    
    def action_quit(self):
        """Exit the application"""
        self.exit()

def main():
    while True:
        # Get search parameters from user
        query = Prompt.ask("[bold]Enter your search query[/bold]")
        search_type = Prompt.ask(
            "[bold]Search for[/bold]",
            choices=["track", "album(not supported yet)"]
        )
        
        if search_type == "album":
            print("[yellow]Only track browsing is supported for selection. Defaulting to 'track'.[/yellow]")
            search_type = "track"
        
        # print(f"[bold green]Fetching all results for '{query}' ({search_type})...[/bold green]")
        all_results = fetch_all_results(query, search_type)
        # print(f"[bold green]Fetched {len(all_results)} items.[/bold green]")
        
        if not all_results:
            print("[red]No results found. Try another search.[/red]")
            continue
        
        # Run the app
        app = Results(all_results, search_type, query)
        exit_code = app.run()
        
        # Always loop back for a new search
        continue_search = Prompt.ask(
            "[bold]Search again?[/bold]",
            choices=["y", "n"],
        )
        if continue_search.lower() != "y":
            break

if __name__ == "__main__":
    main()
