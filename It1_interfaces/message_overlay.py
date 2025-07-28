# MessageOverlay.py - Displays game messages and notifications
import cv2
import numpy as np
import time
from typing import Optional, List
from dataclasses import dataclass
from It1_interfaces.EventSystem import Event, EventType, event_publisher

@dataclass
class Message:
    text: str
    start_time: float
    duration: float
    font_size: float = 1.0
    color: tuple = (255, 255, 255)
    background_color: tuple = (0, 0, 0, 180)
    fade_in_duration: float = 0.5
    fade_out_duration: float = 0.5

class MessageOverlay:
    """Component that displays temporary messages and game notifications."""
    
    def __init__(self):
        self.messages: List[Message] = []
        self.current_time = time.time()
        
        # Subscribe to relevant events
        event_publisher.subscribe(EventType.GAME_START, self.on_game_start)
        event_publisher.subscribe(EventType.GAME_END, self.on_game_end)
        event_publisher.subscribe(EventType.KING_CAPTURED, self.on_king_captured)
        event_publisher.subscribe(EventType.PAWN_PROMOTED, self.on_pawn_promoted)
        
        print("💬 MessageOverlay initialized and subscribed to events")
    
    def on_game_start(self, event: Event):
        """Handle game start event."""
        player1_name = event.data.get('player1_name', 'Player 1')
        player2_name = event.data.get('player2_name', 'Player 2')
        
        messages = [
            f"🎮 Chess Game Starting! 🎮",
            f"⚪ {player1_name} (White) vs ⚫ {player2_name} (Black)",
            f"🎯 Player 1: Use number keys (8↑ 2↓ 4← 6→) + Enter to select",
            f"🎯 Player 2: Use WASD keys + Space to select",
            f"🏆 Capture the enemy King to win!",
            f"Good luck and have fun! ✨"
        ]
        
        start_delay = 0
        for i, msg in enumerate(messages):
            self.show_message(msg, duration=3.0, delay=start_delay)
            start_delay += 0.5  # Stagger messages
        
        print("💬 Displayed game start messages")
    
    def on_game_end(self, event: Event):
        """Handle game end event."""
        winner = event.data.get('winner', 'Unknown')
        winning_reason = event.data.get('reason', 'King captured')
        
        messages = [
            f"🎉 GAME OVER! 🎉",
            f"🏆 Winner: {winner}! 🏆",
            f"📋 Reason: {winning_reason}",
            f"🎮 Press Q or ESC to exit",
            f"Thanks for playing! 🌟"
        ]
        
        start_delay = 0
        for i, msg in enumerate(messages):
            if i == 0:  # Game over message - make it prominent
                self.show_message(msg, duration=5.0, font_size=1.5, 
                                color=(0, 255, 0), delay=start_delay)
            elif i == 1:  # Winner message
                self.show_message(msg, duration=5.0, font_size=1.2, 
                                color=(255, 215, 0), delay=start_delay)  # Gold color
            else:
                self.show_message(msg, duration=4.0, delay=start_delay)
            start_delay += 0.8
        
        print(f"💬 Displayed game end messages for winner: {winner}")
    
    def on_king_captured(self, event: Event):
        """Handle king capture event."""
        king_piece = event.data.get('king_piece', '')
        capturing_piece = event.data.get('capturing_piece', '')
        
        king_color = "White" if 'W' in king_piece else "Black"
        captor_color = "Black" if 'B' in capturing_piece else "White"
        
        messages = [
            f"👑💀 KING CAPTURED! 💀👑",
            f"⚔️ {captor_color} captures {king_color} King!",
            f"🎯 {capturing_piece} takes {king_piece}!"
        ]
        
        start_delay = 0
        for msg in messages:
            self.show_message(msg, duration=3.0, font_size=1.3, 
                            color=(255, 0, 0), delay=start_delay)  # Red for dramatic effect
            start_delay += 0.3
        
        print(f"💬 Displayed king capture messages")
    
    def on_pawn_promoted(self, event: Event):
        """Handle pawn promotion event."""
        pawn_piece = event.data.get('pawn_piece', '')
        new_piece = event.data.get('new_piece', '')
        position = event.data.get('position', (0, 0))
        
        pawn_color = "White" if 'W' in pawn_piece else "Black"
        pos_notation = f"{chr(ord('a') + position[0])}{8 - position[1]}"
        
        messages = [
            f"👑✨ PAWN PROMOTION! ✨👑",
            f"🎉 {pawn_color} pawn becomes Queen at {pos_notation}!",
            f"🔥 {pawn_piece} → {new_piece}"
        ]
        
        start_delay = 0
        for msg in messages:
            self.show_message(msg, duration=2.5, font_size=1.1, 
                            color=(255, 215, 0), delay=start_delay)  # Gold color
            start_delay += 0.4
        
        print(f"💬 Displayed pawn promotion messages")
    
    def show_message(self, text: str, duration: float = 3.0, font_size: float = 1.0, 
                    color: tuple = (255, 255, 255), background_color: tuple = (0, 0, 0, 180),
                    delay: float = 0.0):
        """Show a temporary message."""
        current_time = time.time()
        message = Message(
            text=text,
            start_time=current_time + delay,
            duration=duration,
            font_size=font_size,
            color=color,
            background_color=background_color
        )
        self.messages.append(message)
        print(f"💬 Queued message: '{text}' for {duration}s")
    
    def update(self, current_time: float):
        """Update message system and remove expired messages."""
        self.current_time = current_time
        
        # Remove expired messages
        self.messages = [msg for msg in self.messages 
                        if current_time < msg.start_time + msg.duration + msg.fade_out_duration]
    
    def draw_on_image(self, img: np.ndarray):
        """Draw all active messages on the image."""
        if not self.messages:
            return
        
        height, width = img.shape[:2]
        current_time = time.time()
        
        # Calculate message positions (centered, stacked vertically)
        active_messages = [msg for msg in self.messages 
                          if current_time >= msg.start_time and 
                             current_time < msg.start_time + msg.duration + msg.fade_out_duration]
        
        if not active_messages:
            return
        
        # Start from center, work outward
        y_center = height // 2
        message_height = 60  # Spacing between messages
        total_height = len(active_messages) * message_height
        start_y = y_center - (total_height // 2)
        
        for i, message in enumerate(active_messages):
            self._draw_message(img, message, start_y + i * message_height, current_time)
    
    def _draw_message(self, img: np.ndarray, message: Message, y_pos: int, current_time: float):
        """Draw a single message with fade effects."""
        # Calculate alpha based on fade in/out
        elapsed = current_time - message.start_time
        alpha = 1.0
        
        if elapsed < message.fade_in_duration:
            # Fade in
            alpha = elapsed / message.fade_in_duration
        elif elapsed > message.duration - message.fade_out_duration:
            # Fade out
            remaining = message.start_time + message.duration - current_time
            alpha = remaining / message.fade_out_duration
        
        alpha = max(0.0, min(1.0, alpha))
        if alpha <= 0:
            return
        
        # Get text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = message.font_size
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(message.text, font, font_scale, thickness)
        
        # Calculate position (centered)
        height, width = img.shape[:2]
        x_pos = (width - text_width) // 2
        
        # Draw background rectangle with transparency
        if len(message.background_color) == 4:  # RGBA
            bg_alpha = (message.background_color[3] / 255.0) * alpha
        else:  # RGB
            bg_alpha = alpha * 0.7
        
        # Create background overlay
        overlay = img.copy()
        padding = 20
        cv2.rectangle(overlay, 
                     (max(0, x_pos - padding), max(0, y_pos - text_height - padding)),
                     (min(width, x_pos + text_width + padding), min(height, y_pos + baseline + padding)),
                     message.background_color[:3], -1)
        
        # Blend overlay with original image
        cv2.addWeighted(overlay, bg_alpha, img, 1 - bg_alpha, 0, img)
        
        # Draw text with alpha
        text_color = tuple(int(c * alpha) for c in message.color)
        cv2.putText(img, message.text, (x_pos, y_pos), font, font_scale, text_color, thickness, cv2.LINE_AA)
    
    def clear_all_messages(self):
        """Clear all messages."""
        self.messages.clear()
        print("💬 Cleared all messages")
    
    def has_active_messages(self) -> bool:
        """Check if there are any active messages."""
        current_time = time.time()
        return any(current_time >= msg.start_time and 
                  current_time < msg.start_time + msg.duration + msg.fade_out_duration 
                  for msg in self.messages)