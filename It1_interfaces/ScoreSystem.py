# ScoreSystem.py - Tracks and displays game score based on captured pieces
from typing import Dict
import cv2
import numpy as np
from It1_interfaces.EventSystem import Event, EventType, event_publisher

class ScoreSystem:
    """Component that tracks and displays game score based on captured pieces."""
    
    # Piece values according to chess standards
    PIECE_VALUES = {
        'P': 1,  # Pawn
        'N': 3,  # Knight
        'B': 3,  # Bishop
        'R': 5,  # Rook
        'Q': 9,  # Queen
        'K': 0   # King (game ends when captured)
    }
    
    def __init__(self, player1_name: str = "Player 1", player2_name: str = "Player 2"):
        self.player1_name = player1_name  # White pieces
        self.player2_name = player2_name  # Black pieces
        self.player1_score = 0  # White's score (captured black pieces)
        self.player2_score = 0  # Black's score (captured white pieces)
        
        self.player1_captured: Dict[str, int] = {}  # Count of each piece type captured by white
        self.player2_captured: Dict[str, int] = {}  # Count of each piece type captured by black
        
        # Subscribe to relevant events
        event_publisher.subscribe(EventType.PIECE_CAPTURED, self.on_piece_captured)
        event_publisher.subscribe(EventType.GAME_START, self.on_game_start)
        
        print("🏆 ScoreSystem initialized and subscribed to events")
    
    def on_game_start(self, event: Event):
        """Handle game start event."""
        self.player1_score = 0
        self.player2_score = 0
        self.player1_captured.clear()
        self.player2_captured.clear()
        print("🏆 ScoreSystem: Game started - reset scores")
    
    def on_piece_captured(self, event: Event):
        """Handle piece capture event."""
        captured_piece = event.data.get('captured_piece', '')
        capturing_piece = event.data.get('capturing_piece', '')
        
        if not captured_piece or not capturing_piece:
            print("⚠️ ScoreSystem: Missing piece information in capture event")
            return
        
        # Get piece type from piece ID (first character after color)
        captured_type = captured_piece[0] if len(captured_piece) > 0 else 'P'

        # captured_type = captured_piece[1] if len(captured_piece) > 1 else 'P'
        piece_value = self.PIECE_VALUES.get(captured_type, 0)
        
        # Determine which player made the capture
        capturing_is_white = 'W' in capturing_piece
        captured_is_white = 'W' in captured_piece
        
        if capturing_is_white and not captured_is_white:
            # White captured black piece
            self.player1_score += piece_value
            self.player1_captured[captured_type] = self.player1_captured.get(captured_type, 0) + 1
            print(f"🏆 {self.player1_name} scored {piece_value} points for capturing {captured_piece}")
            
        elif not capturing_is_white and captured_is_white:
            # Black captured white piece
            self.player2_score += piece_value
            self.player2_captured[captured_type] = self.player2_captured.get(captured_type, 0) + 1
            print(f"🏆 {self.player2_name} scored {piece_value} points for capturing {captured_piece}")
    
    def get_score_difference(self) -> int:
        """Get score difference (positive if player1 ahead, negative if player2 ahead)."""
        return self.player1_score - self.player2_score
    
    def get_leading_player(self) -> str:
        """Get name of leading player."""
        diff = self.get_score_difference()
        if diff > 0:
            return self.player1_name
        elif diff < 0:
            return self.player2_name
        else:
            return "Tied"
    
    def draw_on_image(self, img: np.ndarray, x: int, y: int, width: int, height: int):
        """Draw score display on the given image."""
        # Draw background
        cv2.rectangle(img, (x, y), (x + width, y + height), (250, 250, 250), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # Draw header
        header_height = 30
        cv2.rectangle(img, (x, y), (x + width, y + header_height), (220, 220, 220), -1)
        cv2.putText(img, "Score", (x + width//2 - 25, y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Player 1 (White) section
        p1_y = y + header_height + 10
        cv2.putText(img, f"{self.player1_name} (W)", (x + 10, p1_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, f"Score: {self.player1_score}", (x + 10, p1_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Show captured pieces for player 1
        captured_y = p1_y + 40
        captured_text = "Captured: "
        for piece_type, count in self.player1_captured.items():
            if count > 0:
                captured_text += f"{piece_type}×{count} "
        if len(captured_text) > 10:  # If there are captures
            cv2.putText(img, captured_text, (x + 10, captured_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 100), 1)
        
        # Divider line
        mid_y = y + height // 2
        cv2.line(img, (x + 10, mid_y), (x + width - 10, mid_y), (150, 150, 150), 1)
        
        # Player 2 (Black) section
        p2_y = mid_y + 20
        cv2.putText(img, f"{self.player2_name} (B)", (x + 10, p2_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, f"Score: {self.player2_score}", (x + 10, p2_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Show captured pieces for player 2
        captured_y2 = p2_y + 40
        captured_text2 = "Captured: "
        for piece_type, count in self.player2_captured.items():
            if count > 0:
                captured_text2 += f"{piece_type}×{count} "
        if len(captured_text2) > 10:  # If there are captures
            cv2.putText(img, captured_text2, (x + 10, captured_y2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 100), 1)
        
        # Score difference
        diff = self.get_score_difference()
        if diff != 0:
            diff_y = y + height - 30
            leading = self.get_leading_player()
            cv2.putText(img, f"{leading} leads by {abs(diff)}", (x + 10, diff_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 100, 0), 1)
    
    def get_player1_score(self) -> int:
        return self.player1_score
    
    def get_player2_score(self) -> int:
        return self.player2_score