# MovesLog.py - Tracks and displays move history
from typing import List, Tuple
from dataclasses import dataclass
import cv2
import numpy as np
from It1_interfaces.EventSystem import Event, EventType, event_publisher

@dataclass
class MoveEntry:
    move_number: int
    white_move: str = ""
    black_move: str = ""
    white_time: str = ""
    black_time: str = ""
    def to_dict(self):
        return {
            "move_number": self.move_number,
            "white_move": self.white_move,
            "black_move": self.black_move,
            "white_time": self.white_time,
            "black_time": self.black_time
        }
class MovesLog:
    """Component that tracks and displays chess moves history."""
    
    def __init__(self):
        self.moves: List[MoveEntry] = []
        self.current_move_number = 1
        self.pending_white_move = None
        self.pending_black_move = None
        
        # Subscribe to relevant events
        event_publisher.subscribe(EventType.MOVE_MADE, self.on_move_made)
        event_publisher.subscribe(EventType.PIECE_CAPTURED, self.on_piece_captured)
        event_publisher.subscribe(EventType.GAME_START, self.on_game_start)
        
        print("📝 MovesLog initialized and subscribed to events")
    
    def on_game_start(self, event: Event):
        """Handle game start event."""
        self.moves.clear()
        self.current_move_number = 1
        self.pending_white_move = None
        self.pending_black_move = None
        print("📝 MovesLog: Game started - cleared move history")
    
    def on_move_made(self, event: Event):
        """Handle move made event."""
        piece_id = event.data.get('piece_id', '')
        from_pos = event.data.get('from_position', (0, 0))
        to_pos = event.data.get('to_position', (0, 0))
        timestamp = event.data.get('timestamp', 0)
        
        # Convert positions to chess notation
        move_notation = self._position_to_notation(from_pos, to_pos, piece_id)
        time_str = self._format_time(timestamp)
        
        # Determine if it's a white or black piece
        is_white = 'W' in piece_id
        
        if is_white:
            if self.pending_white_move is None:
                # Start new move entry
                self.pending_white_move = MoveEntry(
                    move_number=self.current_move_number,
                    white_move=move_notation,
                    white_time=time_str
                )
        else:
            if self.pending_white_move is not None:
                # Complete the move entry
                self.pending_white_move.black_move = move_notation
                self.pending_white_move.black_time = time_str
                self.moves.append(self.pending_white_move)
                self.current_move_number += 1
                self.pending_white_move = None
            else:
                # Black moves first (unusual but handle it)
                self.pending_black_move = MoveEntry(
                    move_number=self.current_move_number,
                    black_move=move_notation,
                    black_time=time_str
                )
        
        print(f"📝 MovesLog: Recorded move {move_notation} by {piece_id}")
    
    def on_piece_captured(self, event: Event):
        """Handle piece capture - modify last move notation."""
        captured_piece = event.data.get('captured_piece', '')
        capturing_piece = event.data.get('capturing_piece', '')
        
        # Add capture notation to the last move
        if self.pending_white_move and 'W' in capturing_piece:
            if 'x' not in self.pending_white_move.white_move:
                # Add capture symbol
                parts = self.pending_white_move.white_move.split('-')
                if len(parts) == 2:
                    self.pending_white_move.white_move = f"{parts[0]}x{parts[1]}"
        
        print(f"📝 MovesLog: Updated move notation for capture of {captured_piece}")
    
    def _position_to_notation(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], piece_id: str) -> str:
        """Convert board positions to chess notation."""
        def pos_to_chess(pos):
            x, y = pos
            file = chr(ord('a') + x)
            rank = str(8 - y)
            return f"{file}{rank}"
        
        from_chess = pos_to_chess(from_pos)
        to_chess = pos_to_chess(to_pos)
        
        # Get piece symbol
        piece_symbol = self._get_piece_symbol(piece_id)
        
        return f"{piece_symbol}{from_chess}-{to_chess}"
    
    def _get_piece_symbol(self, piece_id: str) -> str:
        """Get chess notation symbol for piece."""
        if piece_id.startswith('P'):
            return ""  # Pawns don't have symbol
        elif piece_id.startswith('R'):
            return "R"
        elif piece_id.startswith('N'):
            return "N"
        elif piece_id.startswith('B'):
            return "B"
        elif piece_id.startswith('Q'):
            return "Q"
        elif piece_id.startswith('K'):
            return "K"
        return ""
    
    def _format_time(self, timestamp_ms: int) -> str:
        """Format timestamp to MM:SS.mmm format."""
        seconds = timestamp_ms // 1000
        milliseconds = timestamp_ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def draw_on_image(self, img: np.ndarray, x: int, y: int, width: int, height: int):
        """Draw moves log on the given image."""
        # Draw background
        cv2.rectangle(img, (x, y), (x + width, y + height), (240, 240, 240), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # Draw header
        header_height = 30
        cv2.rectangle(img, (x, y), (x + width, y + header_height), (200, 200, 200), -1)
        cv2.putText(img, "Moves Log", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Draw column headers
        col_y = y + header_height + 20
        cv2.putText(img, "Move", (x + 10, col_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        cv2.putText(img, "White", (x + 60, col_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        cv2.putText(img, "Black", (x + 150, col_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Draw moves
        row_height = 20
        start_y = col_y + 10
        max_rows = (height - 60) // row_height
        
        # Show last moves first (scroll effect)
        visible_moves = self.moves[-max_rows:] if len(self.moves) > max_rows else self.moves
        
        for i, move in enumerate(visible_moves):
            row_y = start_y + (i * row_height)
            
            # Move number
            cv2.putText(img, f"{move.move_number}.", (x + 10, row_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            
            # White move
            if move.white_move:
                cv2.putText(img, move.white_move, (x + 60, row_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            
            # Black move
            if move.black_move:
                cv2.putText(img, move.black_move, (x + 150, row_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
        
        # Show current pending move
        if self.pending_white_move:
            row_y = start_y + (len(visible_moves) * row_height)
            if row_y < y + height - 20:
                cv2.putText(img, f"{self.pending_white_move.move_number}.", (x + 10, row_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 100), 1)
                cv2.putText(img, self.pending_white_move.white_move, (x + 60, row_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 100), 1)
    
    def get_moves_count(self) -> int:
        """Get total number of completed moves."""
        return len(self.moves)