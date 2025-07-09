"""
Audio playback functionality using VLC.
"""
import vlc
import time
import threading
from ..config import console

class AudioPlayer:
    """Audio player class that handles playback using VLC."""

    def __init__(self):
        """Initialize VLC instance and player."""
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
        """
        Start playing audio from the given URL.

        Args:
            url: Audio stream URL
        """
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
                        console.print(f"Error in position callback: {e}")

                # Check if track has ended
                state = self.player.get_state()
                if state == vlc.State.Ended or (duration_ms > 0 and position_ms >= duration_ms - 500):
                    if self._on_end_callback:
                        try:
                            self._on_end_callback()
                        except Exception as e:
                            console.print(f"Error in end callback: {e}")
                    break

            # Sleep briefly to avoid consuming too much CPU
            time.sleep(0.25)

    def set_position_callback(self, callback):
        """
        Set the callback function for position updates.

        Args:
            callback: Function to call with position updates (position_sec, duration_sec)
        """
        self._position_callback = callback

    def set_on_end_callback(self, callback):
        """
        Set the callback function for end of playback.

        Args:
            callback: Function to call when playback ends
        """
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
        """
        Get the current playback position in seconds.

        Returns:
            Current position in seconds
        """
        if not self.is_playing:
            return 0
        time_ms = self.player.get_time()
        return time_ms / 1000 if time_ms >= 0 else 0

    def get_duration(self):
        """
        Get the total duration in seconds.

        Returns:
            Total duration in seconds
        """
        if not self.is_playing:
            return 0
        length_ms = self.player.get_length()
        return length_ms / 1000 if length_ms > 0 else 0

    def is_currently_playing(self):
        """
        Check if player is currently playing (not paused or stopped).

        Returns:
            True if playing, False otherwise
        """
        return self.is_playing and not self.is_paused
