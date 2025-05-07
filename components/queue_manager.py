"""
Queue manager component for DAB Terminal Music Player.
Handles track queuing functionality.
"""
from typing import List, Dict, Optional, Callable
from rich.console import Console

console = Console()

class QueueManager:
    """Manages the playback queue for the music player."""
    
    def __init__(self):
        """Initialize an empty queue."""
        self._queue: List[Dict] = []
        self._current_index: int = -1
        self._on_queue_change_callback: Optional[Callable] = None
        
    @property
    def queue(self) -> List[Dict]:
        """Return the current queue."""
        return self._queue
        
    @property
    def current_index(self) -> int:
        """Return the current track index."""
        return self._current_index
    
    @property
    def current_track(self) -> Optional[Dict]:
        """Return the current track or None if queue is empty."""
        if 0 <= self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None
    
    def add_track(self, track: Dict) -> None:
        """
        Add a track to the queue.
        
        Args:
            track: Track information dictionary
        """
        self._queue.append(track)
        # If this is the first track, set current index to 0
        if len(self._queue) == 1:
            self._current_index = 0
        self._notify_queue_change()
        
    def remove_track(self, index: int) -> bool:
        """
        Remove a track from the queue by index.
        
        Args:
            index: Index of track to remove
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self._queue):
            # Adjust current index if needed
            if index == self._current_index:
                # If removing current track, don't change current_index
                # We'll just remove the track, and the next track will take its place
                pass
            elif index < self._current_index:
                # If removing track before current, adjust index down
                self._current_index -= 1
            
            # Remove the track
            self._queue.pop(index)
            
            # If queue is now empty, reset current index
            if not self._queue:
                self._current_index = -1
            # If we removed the last track and current_index is now out of bounds
            elif self._current_index >= len(self._queue):
                self._current_index = len(self._queue) - 1
                
            self._notify_queue_change()
            return True
        return False
    
    def clear_queue(self) -> None:
        """Clear the entire queue."""
        self._queue = []
        self._current_index = -1
        self._notify_queue_change()
    
    def next_track(self) -> Optional[Dict]:
        """
        Move to the next track in the queue.
        
        Returns:
            The next track or None if at the end of the queue
        """
        if not self._queue:
            return None
        
        if self._current_index < len(self._queue) - 1:
            self._current_index += 1
            self._notify_queue_change()
            return self._queue[self._current_index]
        return None
    
    def previous_track(self) -> Optional[Dict]:
        """
        Move to the previous track in the queue.
        
        Returns:
            The previous track or None if at the beginning of the queue
        """
        if not self._queue:
            return None
        
        if self._current_index > 0:
            self._current_index -= 1
            self._notify_queue_change()
            return self._queue[self._current_index]
        return None
    
    def move_track(self, from_index: int, to_index: int) -> bool:
        """
        Move a track from one position to another in the queue.
        
        Args:
            from_index: Current index of the track
            to_index: Destination index for the track
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
            # Save the track and remove from current position
            track = self._queue.pop(from_index)
            
            # Track the current track if it's being moved
            is_current = from_index == self._current_index
            
            # Adjust current_index if needed
            if is_current:
                self._current_index = to_index
            elif from_index < self._current_index and to_index >= self._current_index:
                self._current_index -= 1
            elif from_index > self._current_index and to_index <= self._current_index:
                self._current_index += 1
                
            # Insert track at new position
            self._queue.insert(to_index, track)
            self._notify_queue_change()
            return True
        return False
    
    def set_on_queue_change_callback(self, callback: Callable) -> None:
        """
        Set callback for when queue changes.
        
        Args:
            callback: Function to call when queue changes
        """
        self._on_queue_change_callback = callback
        
    def _notify_queue_change(self) -> None:
        """Notify listeners that the queue has changed."""
        if self._on_queue_change_callback:
            try:
                self._on_queue_change_callback(self)
            except Exception as e:
                console.print(f"Error in queue change callback: {e}")