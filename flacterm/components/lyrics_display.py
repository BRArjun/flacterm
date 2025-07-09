"""
Lyrics display component for showing synchronized lyrics.
"""
import re
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import ScrollableContainer
from ..config import console

class LyricsDisplay(Widget):
    """Widget for displaying synchronized lyrics."""

    def compose(self):
        """Compose the widget."""
        self.scroll = ScrollableContainer(id="lyrics_display")
        yield self.scroll

    def on_mount(self):
        """Initialize the widget when mounted."""
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
            console.print("lrclib package not found. Please install it with: pip install lrclibapi")
            self.lrclib_available = False

    def parse_lyrics(self, raw_lyrics: str):
        """
        Parse LRC format lyrics.

        Args:
            raw_lyrics: Raw LRC format lyrics text
        """
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
        """Update the lyrics content in the UI."""
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
        """
        Fetch lyrics for a track.

        Args:
            artist: Artist name
            title: Track title
            album: Album name (optional)
            duration: Track duration in seconds (optional)

        Returns:
            True if lyrics were found, False otherwise
        """
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
            console.print(f"Error fetching lyrics: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error fetching lyrics: {str(e)}"))
            self.scroll.refresh()

        self.has_lyrics = False
        self.update_content()
        return False

    async def highlight_line(self, index: int):
        """
        Highlight the current line and scroll to it.

        Args:
            index: Index of the line to highlight
        """
        if not self.line_widgets or len(self.line_widgets) != len(self.lyrics_lines):
            console.print("Line widgets and lyrics lines don't match!")
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
        """
        Search for lyrics using a general query.

        Args:
            query: Search query string

        Returns:
            List of search results or None if no results
        """
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
            console.print(f"Failed to search lyrics: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error searching lyrics: {str(e)}"))
            self.scroll.refresh()
            return None

    def get_lyrics_by_result(self, result_index, results):
        """
        Get lyrics from a specific search result.

        Args:
            result_index: Index of the result to use
            results: List of search results

        Returns:
            True if lyrics were found, False otherwise
        """
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
            console.print(f"Failed to fetch lyrics from result: {e}")
            self.scroll.remove_children()
            self.scroll.mount(Static(f"Error fetching lyrics: {str(e)}"))
            self.scroll.refresh()
            return False

    def update_position(self, position_seconds: float):
        """
        Highlight the current lyrics line based on the song's progress.

        Args:
            position_seconds: Current playback position in seconds
        """
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
