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
            "h     Show/hide this help screen\n"
            "l     Toggle lyrics\n"
            "space Play/pause\n"
            "->    Next page\n"
            "<-    Previous page\n"
            "q     Quit\n"
            "s     Show track info\n"
            "/     Start a new search\n"
            "Esc   Stop playback\n"
            "b     Fast forward 5 seconds\n"
            "v     Rewind 5 seconds\n"
            "Enter Submit new search\n"
            "r     Toggle repeat mode\n"
            "a     Add current track to queue\n"
            "y     Remove track from queue\n"
            "t     Show/hide queue display\n"
            "c     Clear queue\n"
            "m     Show playlists\n"
            "d     Download hovered track\n"
            "k	   Play from queue\n"
            "e     Return to normal results\n"
            "^a    Add hovered song to playlist\n"
            "^r    Remove hovered song from playlist\n"
        )

    def render(self):
        """
        Render the keybindings panel.
        
        Returns:
            Rich Panel with keybindings
        """
        return Panel(self.get_keybinds_text(), title="Keybindings", border_style="cyan")
