"""
Component to display keyboard shortcuts help.
"""
from rich.panel import Panel
from textual.widgets import Static

class KeybindsDisplay(Static):
    """Widget for displaying keyboard shortcuts help."""
    
    def get_keybinds_text(self) -> str:
        """
        Get the text describing all available keybindings.
        
        Returns:
            Formatted keybindings text
        """
        return (
            "[b]Available Keybindings:[/b]\n\n"
            "v     Show/hide this help screen\n"
            "l     Toggle lyrics\n"
            "space Play/pause\n"
            "n     Next page\n"
            "p     Previous page\n"
            "q     Quit\n"
            "s     Show track info\n"
            "/     Start a new search\n"
            "Esc   Stop playback\n"
            "h     Fast forward 5 seconds\n"
            "g     Rewind 5 seconds\n"
            "^s    Submit new search\n"
            "r     Toggle repeat mode\n"
            "a     Add current track to queue\n"
            "d     Remove track from queue\n"
            "Q     Show/hide queue display\n"
            "N     Play next track in queue\n"
            "P     Play previous track in queue\n"
            "C     Clear queue\n"
        )

    def render(self):
        """
        Render the keybindings panel.
        
        Returns:
            Rich Panel with keybindings
        """
        return Panel(self.get_keybinds_text(), title="Keybindings", border_style="cyan")