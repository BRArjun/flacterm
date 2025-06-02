#!/usr/bin/env python3
"""
DAB Terminal Music Player
A terminal-based music player using the DAB API and Textual TUI framework.
"""

import sys
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Static, Select, Label
from textual.binding import Binding
from textual.screen import Screen

# Import components
from components.audio_player import AudioPlayer
from components.results import Results
from utils.api import fetch_all_results


class SearchScreen(Screen):
    """Main search interface screen."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "search", "Search", priority=True),
        Binding("escape", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: transparent;
    }

    .main-container {
        layout: horizontal;
        width: 100%;
        height: 100%;
    }

    .left-panel {
        width: 50%;
        height: 100%;
        padding: 4;
        align: center middle;
    }

    .ascii-art {
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
        text-align: center;
    }

    .features {
        width: 100%;
        padding: 1;
        color: $text;
    }

    .features-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .right-panel {
    width: 50%;
    height: 100%;
    padding: 4;
    align: center middle;
    layout: vertical;
    content-align: center middle;
}

.right-panel > * {
    margin-bottom: 1;
}

    .form-label {
        color: $text;
        text-style: bold;
    }

    #search-input,
    #search-type {
        width: 100%;
        min-width: 40;
    }

    .button-group {
    layout: horizontal;
    content-align: center middle;
    margin-top: 1;
}

.button-group > * {
    margin-right: 2;
}

    .search-button {
        min-width: 18;
    }

    #status {
        margin-top: 1;
        text-align: center;
    }

    .error-message {
        color: $error;
    }

    .success-message {
        color: $success;
    }
    """

    def __init__(self):
        super().__init__()
        self.search_input = None
        self.search_type_select = None
        self.search_button = None
        self.status_label = None
        self.is_searching = False

    def compose(self) -> ComposeResult:
        """Compose the search screen layout."""
        with Container(classes="main-container"):

            # Left side: ASCII + features
            with Container(classes="left-panel"):
                yield Static(r"""
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
   ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░     
""", classes="ascii-art")

                with Container(classes="features"):
                    yield Static("Features:", classes="features-title")
                    yield Static("• Search and play high-quality audio tracks")
                    yield Static("• Synchronized lyrics display")
                    yield Static("• Keyboard shortcuts for easy navigation")
                    yield Static("• Track information and playback controls")

            # Right side: Search Form
            with Container(classes="right-panel"):
                yield Label("Search Query:", classes="form-label")
                self.search_input = Input(placeholder="Enter your search query...", id="search-input")
                yield self.search_input

                yield Label("Search Type:", classes="form-label")
                self.search_type_select = Select([
                    ("Track", "track"),
                    ("Album", "album")
                ], value="track", id="search-type")
                yield self.search_type_select

                with Horizontal(classes="button-group"):
                    self.search_button = Button("Search", variant="primary", classes="search-button", id="search-btn")
                    yield self.search_button
                    yield Button("Quit", variant="error", classes="search-button", id="quit-btn")

                self.status_label = Static("", id="status")
                yield self.status_label

    def on_mount(self):
        """Focus the search input when screen loads."""
        self.search_input.focus()
        self.theme = 'gruvbox'

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "search-btn":
            await self.action_search()
        elif event.button.id == "quit-btn":
            self.app.exit()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in search input."""
        if event.input.id == "search-input":
            await self.action_search()

    async def action_search(self) -> None:
        """Perform search action."""
        if self.is_searching:
            return

        query = self.search_input.value.strip()
        if not query:
            self.status_label.update("❌ Search query cannot be empty. Please try again.")
            self.status_label.add_class("error-message")
            return

        search_type = self.search_type_select.value

        # Show album warning if selected
        if search_type == "album":
            self.status_label.update("⚠️ Only track browsing is currently supported. Using 'track' search.")
            search_type = "track"

        # Start searching
        self.is_searching = True
        self.search_button.disabled = True
        self.status_label.update("🔍 Searching...")
        self.status_label.remove_class("error-message")
        self.status_label.add_class("success-message")

        try:
            # Perform search in a thread
            all_results = await asyncio.get_event_loop().run_in_executor(
                None, fetch_all_results, query, search_type
            )

            if not all_results:
                self.status_label.update("❌ No results found. Try another search.")
                self.status_label.remove_class("success-message")
                self.status_label.add_class("error-message")
            else:
                self.status_label.update(f"✅ Found {len(all_results)} results!")
                await self.show_results(all_results, search_type, query)

        except Exception as e:
            self.status_label.update(f"❌ An error occurred: {str(e)}")
            self.status_label.remove_class("success-message")
            self.status_label.add_class("error-message")
        finally:
            self.is_searching = False
            self.search_button.disabled = False

    async def show_results(self, results, search_type, query):
        """Show results in the Results app."""
        self.app.search_results = {
            'results': results,
            'search_type': search_type,
            'query': query
        }
        self.app.show_results_flag = True
        self.app.exit()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class DABMusicPlayerApp(App):
    """Main DAB Music Player application."""

    TITLE = "DAB Terminal Music Player"
    SUB_TITLE = "High-Quality Audio Streaming"

    CSS = """
    DABMusicPlayerApp {
        background: transparent;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.search_results = None
        self.show_results_flag = False

    def on_mount(self) -> None:
        self.push_screen(SearchScreen())
        self.theme = 'gruvbox'

    def check_for_results_transition(self):
        if self.show_results_flag and self.search_results:
            self.show_results_flag = False
            results_app = Results(
                self.search_results['results'],
                self.search_results['search_type'],
                self.search_results['query']
            )
            self.search_results = None
            self.exit()
            results_app.run()
            new_search_app = DABMusicPlayerApp()
            new_search_app.run()


def main():
    try:
        while True:
            app = DABMusicPlayerApp()
            app.run()
            app.check_for_results_transition()
            if not app.show_results_flag:
                break
    except KeyboardInterrupt:
        print("\nProgram terminated by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
