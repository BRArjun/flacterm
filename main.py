#!/usr/bin/env python3
"""
DAB Terminal Music Player
A terminal-based music player using the DAB API and Textual TUI framework.
"""

import sys
import threading
from rich.console import Console
from rich.prompt import Prompt
from textual.app import App

# Import components
from components.audio_player import AudioPlayer
from components.results import Results
from utils.api import fetch_all_results

console = Console()

def show_welcome():
    """Display welcome message and app information."""
    console.print("\n[bold cyan]DAB Terminal Music Player[/bold cyan]")
    console.print("[dim]A terminal-based music player for high-quality audio streaming[/dim]")
    console.print("\n[bold]Features:[/bold]")
    console.print("• Search and play high-quality audio tracks")
    console.print("• Synchronized lyrics display")
    console.print("• Keyboard shortcuts for easy navigation")
    console.print("• Track information and playback controls\n")


def main():
    """Main entry point for the application."""
    show_welcome()
    
    while True:
        try:
            # Get search query from user
            query = Prompt.ask("[bold]Enter your search query[/bold]")
            if not query.strip():
                console.print("[yellow]Search query cannot be empty. Please try again.[/yellow]")
                continue
                
            # Get search type (track only for now)
            search_type = Prompt.ask(
                "[bold]Search for[/bold]", 
                choices=["track", "album"], 
                default="track"
            )
            
            if search_type == "album":
                console.print("[yellow]Only track browsing is currently supported. Defaulting to 'track'.[/yellow]")
                search_type = "track"
            
            # Show searching indicator
            with console.status("[bold green]Searching...[/bold green]"):
                all_results = fetch_all_results(query, search_type)
            
            if not all_results:
                console.print("[red]No results found. Try another search.[/red]")
                continue
                
            console.print(f"[green]Found {len(all_results)} results![/green]")
            
            # Create and run the main UI app
            app = Results(all_results, search_type, query)
            app.run()
            
            # Ask if user wants to continue after exiting the app
            continue_search = Prompt.ask(
                "[bold]Do you want to search again?[/bold]", 
                choices=["y", "n"],
                default="y"
            )
            
            if continue_search.lower() != "y":
                console.print("[bold cyan]Thanks for using DAB Terminal! Goodbye![/bold cyan]")
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Search interrupted. Exiting...[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]An error occurred:[/bold red] {str(e)}")
            console.print("[yellow]Restarting search...[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold]Program terminated by user. Goodbye![/bold]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        sys.exit(1)