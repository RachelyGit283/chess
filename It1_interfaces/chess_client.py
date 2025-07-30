import asyncio
import websockets
import json
import cv2
import numpy as np
import pathlib
import threading
import queue
from typing import Dict, List, Tuple, Optional
import time

# Import your existing classes
import sys
sys.path.append(str(pathlib.Path(__file__).parent))

from It1_interfaces.Board import Board
from It1_interfaces.img import Img
from It1_interfaces.PieceFactory import PieceFactory


class ChessGameClient:
    def __init__(self, server_url="ws://localhost:8765"):
        """Initialize the chess game client."""
        self.server_url = server_url
        self.websocket = None
        self.game_id = None
        self.player_color = None
        self.board = None
        self.pieces_data = []
        self.current_turn = "white"
        self.game_over = False
        self.winner = None
        
        # UI state
        self.selected_piece = None
        self.cursor_pos = [0, 0]
        self.window_name = "Chess Client"
        
        # Message queue for UI updates
        self.message_queue = queue.Queue()
        self.running = True
        
        # Initialize board and graphics
        self._setup_board()
        
        print("🎮 Chess Client initialized")
        print(f"🌐 Ready to connect to: {server_url}")

    def _setup_board(self):
        """Setup the game board and graphics."""
        try:
            # Load board image
            img = Img()
            img_path = pathlib.Path(__file__).parent.parent / "board.png"
            img.read(str("C:/Users/board.png"), size=(822, 822))
            
            if img.img is None:
                raise RuntimeError("Board image failed to load!")
            
            # Create board
            self.board = Board(
                cell_H_pix=103.5,
                cell_W_pix=102.75,
                cell_H_m=1,
                cell_W_m=1,
                W_cells=8,
                H_cells=8,
                img=img
            )
            
            print("📸 Board loaded successfully")
            
        except Exception as e:
            print(f"❌ Error setting up board: {e}")
            raise

    # async def connect_to_server(self):
    #     """Connect to the game server."""
    #     try:
    #         print(f"🔗 Connecting to server: {self.server_url}")
    #         self.websocket = await websockets.connect(self.server_url)
    #         print("✅ Connected to server!")
    #         print("⏳ Waiting for opponent...")
            
    #         # Start message handler
    #         await self._handle_server_messages()
            
    #     except Exception as e:
    #         print(f"❌ Failed to connect to server: {e}")
    #         raise

    async def connect_to_server(self):
        """Connect to the game server with error handling."""
        try:
            print(f"🔗 Connecting to server: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            print("✅ Connected to server!")
            print("⏳ Waiting for opponent...")

            # Start message handler
            await self._handle_server_messages()

        except websockets.exceptions.ConnectionClosed as e:
            print(f"⚠️ Connection closed: code={e.code}, reason={e.reason}")

        except ConnectionRefusedError:
            print("❌ Server refused connection. Is the server running?")

        except Exception as e:
            print(f"🔥 Unexpected error: {e.__class__.__name__}: {e}")

    async def _handle_server_messages(self):
        """Handle messages from server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_server_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection to server lost")
            self.running = False
        except Exception as e:
            print(f"❌ Error handling server messages: {e}")
            self.running = False

    async def _process_server_message(self, data):
        """Process message from server."""
        message_type = data.get("type")
        
        if message_type == "game_started":
            self.game_id = data.get("game_id")
            self.player_color = data.get("player_color")
            opponent = data.get("opponent")
            
            print(f"🎮 Game started! ID: {self.game_id}")
            print(f"🎨 You are playing as: {self.player_color}")
            print(f"👥 Opponent: {opponent}")
            
            # Update cursor position based on player color
            if self.player_color == "white":
                self.cursor_pos = [0, 7]  # Start near white pieces
            else:
                self.cursor_pos = [0, 0]  # Start near black pieces
            
            # Queue UI update
            self.message_queue.put(("game_started", data))
            
        elif message_type == "board_state":
            self.pieces_data = data.get("pieces", [])
            self.current_turn = data.get("current_turn", "white")
            self.game_over = data.get("game_over", False)
            self.winner = data.get("winner")
            
            # Queue UI update
            self.message_queue.put(("board_update", data))
            
        elif message_type == "selection_update":
            # Handle piece selection updates
            self.message_queue.put(("selection_update", data))
            
        elif message_type == "game_over":
            self.winner = data.get("winner")
            self.game_over = True
            print(f"🏆 Game Over! Winner: {self.winner}")
            self.message_queue.put(("game_over", data))
            
        elif message_type == "error":
            error_msg = data.get("message", "Unknown error")
            print(f"❌ Server error: {error_msg}")
            self.message_queue.put(("error", data))
            
        elif message_type == "player_disconnected":
            print("👋 Opponent disconnected")
            self.message_queue.put(("opponent_disconnected", data))
        
        else:
            print(f"❓ Unknown message type: {message_type}")

    async def send_move(self, piece_id, target):
        """Send move to server."""
        if not self.websocket:
            return
            
        move_data = {
            "type": "move",
            "piece_id": piece_id,
            "target": list(target)
        }
        
        try:
            await self.websocket.send(json.dumps(move_data))
            print(f"📤 Sent move: {piece_id} to {target}")
        except Exception as e:
            print(f"❌ Error sending move: {e}")

    async def send_piece_selection(self, position):
        """Send piece selection to server."""
        if not self.websocket:
            return
            
        selection_data = {
            "type": "select_piece",
            "position": list(position)
        }
        
        try:
            await self.websocket.send(json.dumps(selection_data))
            print(f"📤 Sent selection: {position}")
        except Exception as e:
            print(f"❌ Error sending selection: {e}")

    def start_ui_thread(self):
        """Start the UI thread for handling graphics and input."""
        ui_thread = threading.Thread(target=self._run_ui_loop, daemon=True)
        ui_thread.start()
        return ui_thread

    def _run_ui_loop(self):
        """Main UI loop running in separate thread."""
        print("🖼️ Starting UI loop...")
        
        while self.running:
            try:
                # Process server message updates
                while not self.message_queue.empty():
                    try:
                        message_type, data = self.message_queue.get_nowait()
                        self._handle_ui_update(message_type, data)
                    except queue.Empty:
                        break
                
                # Draw current state
                self._draw_board()
                
                # Handle keyboard input
                key = cv2.waitKey(30) & 0xFF
                if key != 255:
                    if self._handle_keyboard_input(key):
                        break  # Exit requested
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.016)  # ~60 FPS
                
            except Exception as e:
                print(f"❌ UI loop error: {e}")
                break
        
        print("🛑 UI loop ended")
        cv2.destroyAllWindows()

    def _handle_ui_update(self, message_type, data):
        """Handle UI updates from server messages."""
        if message_type == "game_started":
            self.window_name = f"Chess Client - {self.player_color.title()} Player"
            
        elif message_type == "board_update":
            # Board state updated - no special action needed, will be drawn
            pass
            
        elif message_type == "game_over":
            winner = data.get("winner")
            if winner == self.player_color:
                print("🎉 You won!")
            else:
                print("😢 You lost!")
            
        elif message_type == "error":
            print(f"⚠️ Server rejected action: {data.get('message')}")

    def _draw_board(self):
        """Draw the current board state."""
        if not self.board:
            return
            
        # Create clean board copy
        display_board = self.board.clone()
        board_img = display_board.img.img
        
        # Draw pieces
        self._draw_pieces(board_img)
        
        # Draw cursor
        self._draw_cursor(board_img)
        
        # Draw game info
        self._draw_game_info(board_img)
        
        # Show the board
        cv2.imshow(self.window_name, board_img)

    def _draw_pieces(self, img):
        """Draw all pieces on the board."""
        cell_width = img.shape[1] // 8
        cell_height = img.shape[0] // 8
        
        for piece_data in self.pieces_data:
            piece_id = piece_data["id"]
            position = piece_data["position"]
            piece_type = piece_data["type"]
            
            if position:
                x, y = position
                
                # Calculate pixel position
                pixel_x = x * cell_width + cell_width // 4
                pixel_y = y * cell_height + cell_height // 4
                
                # Draw piece representation (simplified - you can load actual sprites)
                color = (255, 255, 255) if 'W' in piece_id else (0, 0, 0)
                
                # Draw piece circle
                cv2.circle(img, (pixel_x, pixel_y), 25, color, -1)
                cv2.circle(img, (pixel_x, pixel_y), 25, (128, 128, 128), 2)
                
                # Draw piece type letter
                piece_letter = piece_type[0] if piece_type else 'P'
                cv2.putText(img, piece_letter, (pixel_x - 8, pixel_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                # Highlight selected piece
                if (self.selected_piece and 
                    self.selected_piece.get("id") == piece_id):
                    cv2.rectangle(img, 
                                (x * cell_width, y * cell_height),
                                ((x + 1) * cell_width - 1, (y + 1) * cell_height - 1),
                                (0, 255, 0), 3)

    def _draw_cursor(self, img):
        """Draw player cursor."""
        cell_width = img.shape[1] // 8
        cell_height = img.shape[0] // 8
        
        x, y = self.cursor_pos
        
        # Cursor color based on player
        cursor_color = (255, 0, 0) if self.player_color == "white" else (0, 0, 255)
        
        # Draw cursor rectangle
        cv2.rectangle(img,
                     (x * cell_width, y * cell_height),
                     ((x + 1) * cell_width - 1, (y + 1) * cell_height - 1),
                     cursor_color, 4)

    # def _draw_game_info(self, img):
    #     """Draw game information on the board."""
    #     # Draw player color
    #     color_text = f"Playing as: {self.player_color.upper()}"
    #     cv2.putText(img, color_text, (10, 30),
    #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
    #     # Draw current turn
    #     turn_text = f"Turn: {self.current_turn.upper()}"
    #     turn_color = (0, 255, 0) if self.current_turn == self.player_color else (0, 0, 255)
    #     cv2.putText(img, turn_text, (10, 60),
    #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, turn_color, 2)
        
    #     # Draw game status
    #     if self.game_over:
    #         status_text = f"GAME OVER - Winner: {self.winner.upper()}"
    #         cv2.putText(img, status_text, (10, 90),
    #                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    #     elif self.game_id:
    #         status_text = "GAME ACTIVE"
    #         cv2.putText(img, status_text, (10, 90),
    #                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    #     else:
    #         status_text = "WAITING FOR GAME..."
    #         cv2.putText(img, status_text, (10, 90),
    #                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    def _draw_game_info(self, img):
        """Draw game information on the board."""

        # Draw player color
        player_color = self.player_color.upper() if self.player_color else "UNKNOWN"
        color_text = f"Playing as: {player_color}"
        cv2.putText(img, color_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw current turn
        current_turn = self.current_turn.upper() if self.current_turn else "UNKNOWN"
        turn_text = f"Turn: {current_turn}"
        turn_color = (0, 255, 0) if self.current_turn == self.player_color else (0, 0, 255)
        cv2.putText(img, turn_text, (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, turn_color, 2)

        # Draw game status
        if self.game_over:
            winner = self.winner.upper() if self.winner else "UNKNOWN"
            status_text = f"GAME OVER - Winner: {winner}"
            cv2.putText(img, status_text, (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif self.game_id:
            status_text = "GAME ACTIVE"
            cv2.putText(img, status_text, (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            status_text = "WAITING FOR GAME..."
            cv2.putText(img, status_text, (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    def _handle_keyboard_input(self, key):
        """Handle keyboard input from player."""
        if key == 27 or key == ord('q'):  # ESC or Q
            print("👋 Exiting...")
            self.running = False
            return True
        
        if not self.game_id or self.game_over:
            return False  # No input handling if not in game
        
        # Movement keys
        moved = False
        if key == ord('w') or key == 56:  # W or 8 - UP
            self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
            moved = True
        elif key == ord('s') or key == 50:  # S or 2 - DOWN
            self.cursor_pos[1] = min(7, self.cursor_pos[1] + 1)
            moved = True
        elif key == ord('a') or key == 52:  # A or 4 - LEFT
            self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
            moved = True
        elif key == ord('d') or key == 54:  # D or 6 - RIGHT
            self.cursor_pos[0] = min(7, self.cursor_pos[0] + 1)
            moved = True
        
        if moved:
            print(f"🎯 Cursor moved to: {self.cursor_pos}")
        
        # Selection keys
        if key == 32 or key == 13:  # SPACE or ENTER
            if self.current_turn == self.player_color:
                self._handle_piece_selection()
            else:
                print("⏳ Wait for your turn!")
        
        return False

    def _handle_piece_selection(self):
        """Handle piece selection at cursor position."""
        position = tuple(self.cursor_pos)
        
        # Find piece at cursor position
        piece_at_cursor = None
        for piece_data in self.pieces_data:
            if tuple(piece_data["position"]) == position:
                piece_at_cursor = piece_data
                break
        
        if self.selected_piece is None:
            # Select piece if it belongs to player
            if (piece_at_cursor and 
                self._is_my_piece(piece_at_cursor["id"])):
                self.selected_piece = piece_at_cursor
                print(f"✅ Selected piece: {piece_at_cursor['id']} at {position}")
            else:
                print(f"❌ No valid piece to select at {position}")
        else:
            # Move selected piece or select new piece
            if (piece_at_cursor and 
                self._is_my_piece(piece_at_cursor["id"])):
                # Select different piece
                self.selected_piece = piece_at_cursor
                print(f"✅ Selected different piece: {piece_at_cursor['id']}")
            else:
                # Try to move selected piece
                asyncio.create_task(self._attempt_move(position))
                self.selected_piece = None

    async def _attempt_move(self, target_position):
        """Attempt to move the selected piece."""
        if not self.selected_piece:
            return
        
        piece_id = self.selected_piece["id"]
        current_pos = tuple(self.selected_piece["position"])
        
        print(f"🎯 Attempting move: {piece_id} from {current_pos} to {target_position}")
        
        # Send move to server
        await self.send_move(piece_id, target_position)

    def _is_my_piece(self, piece_id):
        """Check if piece belongs to this player."""
        if self.player_color == "white":
            return 'W' in piece_id
        else:
            return 'B' in piece_id

    def _find_piece_at_position(self, position):
        """Find piece data at given position."""
        for piece_data in self.pieces_data:
            if tuple(piece_data["position"]) == position:
                return piece_data
        return None

    async def disconnect(self):
        """Disconnect from server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from server")


class ChessClientRunner:
    """Runner class to handle async operations."""
    
    def __init__(self, server_url="ws://localhost:8765"):
        self.client = ChessGameClient(server_url)
        self.ui_thread = None

    async def run(self):
        """Run the client."""
        try:
            # Start UI thread
            self.ui_thread = self.client.start_ui_thread()
            
            # Connect to server and handle messages
            await self.client.connect_to_server()
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            # Cleanup
            await self.client.disconnect()
            if self.ui_thread and self.ui_thread.is_alive():
                self.ui_thread.join(timeout=2)


async def main():
    """Main function to run the chess client."""
    print("🎮 Chess Game Client")
    print("=" * 50)
    print("🎯 Controls:")
    print("   WASD or Arrow Keys (8246) - Move cursor")
    print("   SPACE or ENTER - Select piece / Move")
    print("   ESC or Q - Quit")
    print("=" * 50)
    
    # You can change the server URL here if needed
    server_url = "ws://localhost:8765"
    
    runner = ChessClientRunner(server_url)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())