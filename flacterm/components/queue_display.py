from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static
from textual.reactive import reactive
from textual.binding import Binding
from .queue_manager import QueueManager


class QueueDisplay(Static, can_focus=True):
    """Widget for displaying and interacting with the current queue."""
    can_focus = True
    queue_length = reactive(0)
    current_track_index = reactive(-1)

    BINDINGS = [
        Binding("up", "move_up", "Select previous track"),
        Binding("down", "move_down", "Select next track"),
        Binding("enter", "play_selected", "Play selected track"),
    ]

    def __init__(self, queue_manager: QueueManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_manager = queue_manager
        self.queue_manager.set_on_queue_change_callback(self._on_queue_change)

    def _on_queue_change(self, queue_manager):
        self.queue_length = len(queue_manager.queue)
        self.current_track_index = queue_manager.current_index
        self.refresh()

    def render(self):
        table = Table(expand=True, box=None, padding=(0, 1, 0, 1))
        table.add_column("#", justify="right", style="cyan", width=3)
        table.add_column("Title", style="white", ratio=3)
        table.add_column("Artist", style="green", ratio=2)
        table.add_column("Duration", justify="right", style="dim", width=8)

        queue = self.queue_manager.queue
        current_index = self.queue_manager.current_index

        if not queue:
            empty_message = Text("Queue is empty. Add tracks with [a] key.", style="dim")
            table.add_row(Text(""), empty_message, Text(""), Text(""))
            return Panel(table, title="Queue (0)", border_style="cyan")

        for i, track in enumerate(queue):
            title = track.get("title", "Unknown Title")
            artist = track.get("artist", "Unknown Artist")
            duration = track.get("duration", 0)

            if isinstance(duration, (int, float)):
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes}:{seconds:02d}"
            else:
                duration_text = "--:--"

            if i == current_index:
                row_style = "bold white on rgb(40,40,60)"
                index_text = Text("▶", style="bold cyan")
                title_text = Text(title, style="bold white")
                artist_text = Text(artist, style="bold green")
                duration_text = Text(duration_text, style="bold white")
            else:
                row_style = ""
                index_text = Text(f"{i+1}.", style="cyan")
                title_text = Text(title)
                artist_text = Text(artist, style="green")
                duration_text = Text(duration_text, style="dim")

            table.add_row(
                index_text,
                title_text,
                artist_text,
                duration_text,
                style=row_style
            )

        return Panel(
            table,
            title=f"Queue ({len(queue)})",
            border_style="cyan",
            subtitle="[d] Remove  [↑↓] Navigate  [Enter] Play"
        )

    # === ACTIONS ===

    def action_move_up(self):
        if self.queue_manager.queue and self.queue_manager.current_index > 0:
            self.queue_manager.current_index -= 1
            self.refresh()

    def action_move_down(self):
        if self.queue_manager.queue and self.queue_manager.current_index < len(self.queue_manager.queue) - 1:
            self.queue_manager.current_index += 1
            self.refresh()

    def action_play_selected(self):
        index = self.queue_manager.current_index
        if 0 <= index < len(self.queue_manager.queue):
            track = self.queue_manager.queue[index]
            results = self.app.query_one("#results", expect_type=True)
            if hasattr(results, "play_track"):
                results.play_track(track)

    def action_remove_selected(self):
        index = self.queue_manager.current_index
        if 0 <= index < len(self.queue_manager.queue):
            self.queue_manager.remove_track(index)
            if self.queue_manager.current_index >= len(self.queue_manager.queue):
                self.queue_manager.current_index = max(0, len(self.queue_manager.queue) - 1)
            self.refresh()
