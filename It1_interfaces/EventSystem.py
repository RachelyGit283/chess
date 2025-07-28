# EventSystem.py - Publisher-Subscriber Pattern Implementation
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
import threading
import time

class EventType(Enum):
    GAME_START = "game_start"
    GAME_END = "game_end"
    MOVE_MADE = "move_made"
    PIECE_CAPTURED = "piece_captured"
    PIECE_MOVE_START = "piece_move_start"
    PIECE_MOVE_END = "piece_move_end"
    KING_CAPTURED = "king_captured"
    PAWN_PROMOTED = "pawn_promoted"

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: int

class EventPublisher:
    """Publisher that manages subscribers and publishes events."""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            print(f"📡 Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from specific event type."""
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    print(f"📡 Unsubscribed from {event_type.value}")
    
    def publish(self, event_type: EventType, data: Dict[str, Any] = None):
        """Publish event to all subscribers."""
        if data is None:
            data = {}
        
        event = Event(
            type=event_type,
            data=data,
            timestamp=int(time.time() * 1000)
        )
        
        with self._lock:
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"❌ Error in subscriber callback for {event_type.value}: {e}")
        
        print(f"📢 Published event: {event_type.value} with data: {data}")

# Global event publisher instance
event_publisher = EventPublisher()