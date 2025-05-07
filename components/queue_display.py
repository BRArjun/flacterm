"""
Component to display the current queue.
"""
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from components.queue_manager import QueueManager

class QueueDisplay(Static):
    """Widget for displaying the current queue."""
    
    # Use reactive properties to trigger renders when they change
    queue_length = reactive(0)
    current_track_index = reactive(-1)
    
    def __init__(self, queue_manager: QueueManager, *args, **kwargs):
        """
        Initialize the queue display widget.
        
        Args:
            queue_manager: Reference to the queue manager
        """
        super().__init__(*args, **kwargs)
        self.queue_manager = queue_manager
        # Register for queue updates
        self.queue_manager.set_on_queue_change_callback(self._on_queue_change)
        
    def _on_queue_change(self, queue_manager):
        """
        Handle queue change events by updating reactive properties.
        
        Args:
            queue_manager: The queue manager instance
        """
        self.queue_length = len(queue_manager.queue)
        self.current_track_index = queue_manager.current_index
        self.refresh()
        
    def render(self):
        """
        Render the queue panel.
        
        Returns:
            Rich Panel with queue information
        """
        # Create a table for the queue
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
        
        # Add tracks to table
        for i, track in enumerate(queue):
            # Format the track info
            title = track.get("title", "Unknown Title")
            artist = track.get("artist", "Unknown Artist")
            duration = track.get("duration", 0)
            
            # Format duration as mm:ss
            if isinstance(duration, (int, float)):
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes}:{seconds:02d}"
            else:
                duration_text = "--:--"
            
            # Determine row style based on whether this is the current track
            if i == current_index:
                row_style = "bold white on rgb(40,40,60)"
                index_text = Text("▶ ", style="bold cyan")
                title_text = Text(title, style="bold white")
                artist_text = Text(artist, style="bold green")
                duration_text = Text(duration_text, style="bold white")
            else:
                row_style = ""
                index_text = Text(f"{i+1}. ", style="cyan")
                title_text = Text(title)
                artist_text = Text(artist, style="green")
                duration_text = Text(duration_text, style="dim")
            
            # Add the row with appropriate styling
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
            subtitle="[d] Remove  [N/P] Next/Prev"
        )