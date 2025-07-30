# import asyncio
# import websockets
# import json
# import cv2
# import numpy as np
# import pathlib
# import threading
# import time
# from typing import Dict, List, Optional, Tuple

# # Import your existing classes for visualization
# from It1_interfaces.img import Img
# from It1_interfaces.Board import Board
# from It1_interfaces.PieceFactory import PieceFactory
# # ייבוא מערכות הניקוד ורישום המהלכים
# from It1_interfaces.MessageOverlay import MessageOverlay
# from It1_interfaces.ScoreSystem import ScoreSystem
# from It1_interfaces.MovesLog import MovesLog
# from It1_interfaces.SoundSystem import SoundSystem
# from It1_interfaces.EventSystem import Event, EventType, event_publisher

# class ChessClient:
#     def __init__(self, server_uri: str = "ws://localhost:8765"):
#         self.server_uri = server_uri
#         self.websocket = None
#         self.connected = False
#         self.running = True
        
#         # Game state from server
#         self.pieces_data = []
#         self.board_size = (822, 822)
#         self.player1_cursor = [0, 7]
#         self.player2_cursor = [0, 0]
#         self.selected_piece_player1 = None
#         self.selected_piece_player2 = None
#         self.game_over = False
#         self.winner = None
        
#         # Display components
#         self.board = None
#         self.pieces_sprites = {}  # piece_id -> sprite image
#         self.extended_img = None
        
#         # שמות שחקנים
#         self.player1_name = "Player 1"
#         self.player2_name = "Player 2"
        
#         # UI settings (copied from Game.py)
#         self.ui_panel_width = 300
#         self.new_window_width = 822 + self.ui_panel_width + 800
#         self.new_window_height = max(822, 600) + 200
        
#         # ✨ הוספת מערכות הניקוד ורישום המהלכים
#         self.message_overlay = MessageOverlay()
#         self.score_system = ScoreSystem(self.player1_name, self.player2_name)
#         self.moves_log = MovesLog()
#         self.sound_system = SoundSystem()
        
#         print("🎮 Client game systems initialized!")
#         print("💬 MessageOverlay initialized")
#         print("🏆 ScoreSystem initialized")
#         print("📝 MovesLog initialized")
#         print("🔊 SoundSystem initialized")
        
#         self.initialize_display()

#     def initialize_display(self):
#         """אתחול רכיבי התצוגה"""
#         print("📸 Loading board image for client...")
        
#         # טען את תמונת הלוח (בדיוק כמו במain.py)
#         img = Img()
#         img.read(str("C:/Users/board.png"), size=(822, 822))
        
#         if img.img is None:
#             raise RuntimeError("Board image failed to load in client!")
        
#         # צור את הלוח
#         self.board = Board(
#             cell_H_pix=103.5,
#             cell_W_pix=102.75,
#             cell_H_m=1,
#             cell_W_m=1,
#             W_cells=8,
#             H_cells=8,
#             img=img
#         )
        
#         # טען sprites של הכלים
#         self.load_piece_sprites()
        
#         print("🖼️ Display initialized successfully!")

#     def load_piece_sprites(self):
#         """טען את sprites של כל הכלים"""
#         pieces_root = pathlib.Path(r"C:\Users\pieces")
#         piece_types = ["RB", "NB", "BB", "QB", "KB", "PB", "RW", "NW", "BW", "QW", "KW", "PW"]
        
#         for piece_type in piece_types:
#             try:
#                 # טען sprite מתיקיית idle
#                 sprite_path = pieces_root / piece_type / "states" / "idle" / "sprites"
#                 if sprite_path.exists():
#                     # קח את התמונה הראשונה
#                     sprite_files = list(sprite_path.glob("*.png"))
#                     if sprite_files:
#                         sprite_img = Img()
#                         sprite_img.read(str(sprite_files[0]), size=(80, 80))
#                         if sprite_img.img is not None:
#                             self.pieces_sprites[piece_type] = sprite_img
#                             print(f"✅ Loaded sprite for {piece_type}")
#                         else:
#                             print(f"❌ Failed to load sprite for {piece_type}")
#             except Exception as e:
#                 print(f"❌ Error loading sprite for {piece_type}: {e}")

#     async def connect_to_server(self):
#         """התחברות לשרת"""
#         try:
#             print(f"🔌 Connecting to server at {self.server_uri}...")
#             self.websocket = await websockets.connect(self.server_uri)
#             self.connected = True
#             print("✅ Connected to server!")
            
#             # בקש מצב משחק ראשוני
#             await self.request_game_state()
            
#             return True
#         except Exception as e:
#             print(f"❌ Failed to connect to server: {e}")
#             return False

#     async def disconnect_from_server(self):
#         """התנתקות מהשרת"""
#         if self.websocket:
#             await self.websocket.close()
#             self.connected = False
#             print("🔌 Disconnected from server")

#     async def send_keyboard_input(self, key: int):
#         """שליחת קלט מקלדת לשרת"""
#         if not self.connected or not self.websocket:
#             return
            
#         message = {
#             'type': 'keyboard_input',
#             'key': key
#         }
        
#         try:
#             await self.websocket.send(json.dumps(message))
#             print(f"⌨️ Sent key {key} to server")
#         except Exception as e:
#             print(f"❌ Error sending keyboard input: {e}")

#     async def request_game_state(self):
#         """בקשת מצב המשחק מהשרת"""
#         if not self.connected or not self.websocket:
#             return
            
#         message = {'type': 'get_game_state'}
        
#         try:
#             await self.websocket.send(json.dumps(message))
#         except Exception as e:
#             print(f"❌ Error requesting game state: {e}")

#     async def handle_server_message(self, message: str):
#         """טיפול בהודעות מהשרת"""
#         try:
#             data = json.loads(message)
#             msg_type = data.get('type')
            
#             if msg_type == 'game_state':
#                 self.update_game_state(data.get('data', {}))
#             elif msg_type == 'pong':
#                 print("🏓 Received pong from server")
#             # ✨ הוספת טיפול באירועי המשחק
#             elif msg_type == 'game_event':
#                 self.handle_game_event(data.get('event', {}))
#             else:
#                 print(f"❓ Unknown message type: {msg_type}")
                
#         except json.JSONDecodeError:
#             print(f"❌ Invalid JSON from server: {message}")
#         except Exception as e:
#             print(f"❌ Error handling server message: {e}")

#     def handle_game_event(self, event_data):
#         """טיפול באירועי המשחק"""
#         event_type = event_data.get('type')
#         data = event_data.get('data', {})
        
#         if event_type == 'PIECE_CAPTURED':
#             captured_piece = data.get('captured_piece', '')
#             capturing_piece = data.get('capturing_piece', '')
#             position = data.get('position', (0, 0))
            
#             # עדכן ניקוד
#             if 'W' in captured_piece:  # כלי לבן נתפס - שחקן 2 קיבל נקודות
#                 points = self.get_piece_points(captured_piece)
#                 self.score_system.add_score(self.player2_name, points)
#                 print(f"🏆 {self.player2_name} captured {captured_piece} (+{points} points)")
#             elif 'B' in captured_piece:  # כלי שחור נתפס - שחקן 1 קיבל נקודות
#                 points = self.get_piece_points(captured_piece)
#                 self.score_system.add_score(self.player1_name, points)
#                 print(f"🏆 {self.player1_name} captured {captured_piece} (+{points} points)")
            
#             # הצג הודעה
#             self.message_overlay.show_message(f"{capturing_piece} captured {captured_piece}!", 3.0)
            
#         elif event_type == 'MOVE_MADE':
#             piece_id = data.get('piece_id', '')
#             from_pos = data.get('from_position', (0, 0))
#             to_pos = data.get('to_position', (0, 0))
            
#             # רשום את המהלך
#             player_name = self.player1_name if 'W' in piece_id else self.player2_name
#             self.moves_log.add_move(player_name, piece_id, from_pos, to_pos)
            
#         elif event_type == 'PAWN_PROMOTED':
#             pawn_piece = data.get('pawn_piece', '')
#             new_piece = data.get('new_piece', '')
#             self.message_overlay.show_message(f"{pawn_piece} promoted to {new_piece}!", 3.0)
            
#         elif event_type == 'KING_CAPTURED':
#             king_piece = data.get('king_piece', '')
#             self.message_overlay.show_message(f"CHECKMATE! {king_piece} captured!", 5.0)

#     def get_piece_points(self, piece_id):
#         """חישוב נקודות לפי סוג הכלי"""
#         piece_type = ''.join([c for c in piece_id if not c.isdigit()])
#         points_map = {
#             'PW': 1, 'PB': 1,  # חיילים
#             'RW': 5, 'RB': 5,  # צריחים
#             'NW': 3, 'NB': 3,  # סוסים
#             'BW': 3, 'BB': 3,  # רצים
#             'QW': 9, 'QB': 9,  # מלכות
#             'KW': 0, 'KB': 0   # מלכים (אין נקודות כי זה סיום המשחק)
#         }
#         return points_map.get(piece_type, 0)

#     def update_game_state(self, game_data: Dict):
#         """עדכון מצב המשחק מנתוני השרת"""
#         self.pieces_data = game_data.get('pieces', [])
#         self.board_size = tuple(game_data.get('board_size', (822, 822)))
#         self.player1_cursor = game_data.get('player1_cursor', [0, 7])
#         self.player2_cursor = game_data.get('player2_cursor', [0, 0])
#         self.selected_piece_player1 = game_data.get('selected_piece_player1')
#         self.selected_piece_player2 = game_data.get('selected_piece_player2')
#         self.game_over = game_data.get('game_over', False)
#         self.winner = game_data.get('winner')
        
#         # אם המשחק נגמר, הצג הודעת ניצחון
#         if self.game_over and self.winner:
#             print(f"🏆 Game Over! Winner: {self.winner}")
#             self.message_overlay.show_message(f"🏆 {self.winner} WINS! 🏆", 10.0)

#     def draw_game(self):
#         """ציור המשחק - מבוסס על Game._draw()"""
#         if not self.board:
#             return None
            
#         # צור עותק נקי של הלוח
#         display_board = self.board.clone()
        
#         # ציור כל הכלים על העותק
#         self.draw_pieces_on_board(display_board)
        
#         # ציור סמנים של השחקנים
#         self.draw_cursors(display_board)
        
#         # יצירת תמונה מורחבת עם פאנלי הניקוד והמהלכים
#         if hasattr(display_board, "img"):
#             board_img = display_board.img.img
            
#             # יצירת תמונה חדשה גדולה יותר עם כל הפאנלים
#             self.extended_img = self.create_extended_display(board_img)
            
#             # ✨ ציור הודעות על התמונה
#             current_time = time.time()
#             self.message_overlay.update(current_time)
#             self.message_overlay.draw_on_image(self.extended_img)
            
#             return self.extended_img
        
#         return None

#     def draw_pieces_on_board(self, board):
#         """ציור הכלים על הלוח לפי מיקומי הפיקסלים מהשרת"""
#         for piece_data in self.pieces_data:
#             piece_id = piece_data['id']
#             pixel_pos = piece_data.get('pixel_position', (0, 0))
            
#             # חלץ את סוג הכלי מה-ID (למשל "PW0" -> "PW")
#             piece_type = ''.join([c for c in piece_id if not c.isdigit()])
            
#             # מצא את ה-sprite המתאים
#             sprite = self.pieces_sprites.get(piece_type)
#             if sprite and sprite.img is not None:
#                 x, y = pixel_pos
#                 sprite.draw_on(board.img, int(x), int(y))

#     def draw_cursors(self, board):
#         """ציור הסמנים - מועתק מ-Game._draw_cursors()"""
#         if hasattr(board, 'img') and hasattr(board.img, 'img'):
#             img = board.img.img
            
#             # חישוב גודל משבצת
#             board_height, board_width = img.shape[:2]
#             cell_width = board_width // 8
#             cell_height = board_height // 8
            
#             # ציור סמן שחקן 1 (כחול עבה)
#             x1, y1 = self.player1_cursor
#             top_left_1 = (x1 * cell_width, y1 * cell_height)
#             bottom_right_1 = ((x1 + 1) * cell_width - 1, (y1 + 1) * cell_height - 1)
#             cv2.rectangle(img, top_left_1, bottom_right_1, (255, 0, 0), 8)  # כחול BGR
            
#             # ציור סמן שחקן 2 (אדום עבה)
#             x2, y2 = self.player2_cursor
#             top_left_2 = (x2 * cell_width, y2 * cell_height)
#             bottom_right_2 = ((x2 + 1) * cell_width - 1, (y2 + 1) * cell_height - 1)
#             cv2.rectangle(img, top_left_2, bottom_right_2, (0, 0, 255), 8)  # אדום BGR
            
#             # סימון כלי נבחר
#             if self.selected_piece_player1:
#                 piece_pos = self.get_piece_position_by_id(self.selected_piece_player1)
#                 if piece_pos:
#                     px, py = piece_pos
#                     piece_top_left = (px * cell_width, py * cell_height)
#                     piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
#                     cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 0), 4)  # ירוק עבה
            
#             if self.selected_piece_player2:
#                 piece_pos = self.get_piece_position_by_id(self.selected_piece_player2)
#                 if piece_pos:
#                     px, py = piece_pos
#                     piece_top_left = (px * cell_width, py * cell_height)
#                     piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
#                     cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 255), 4)  # צהוב עבה

#     def get_piece_position_by_id(self, piece_id: str) -> Optional[Tuple[int, int]]:
#         """מצא מיקום כלי לפי ID"""
#         for piece_data in self.pieces_data:
#             if piece_data['id'] == piece_id:
#                 return tuple(piece_data.get('position', (0, 0)))
#         return None

#     def create_extended_display(self, board_img):
#         """יצירת תצוגה מורחבת עם פאנלי ניקוד ומהלכים - בדיוק כמו ב-Game.py"""
#         import numpy as np
        
#         # יצירת תמונה חדשה עם גודל מורחב
#         extended_img = np.ones((self.new_window_height, self.new_window_width, 3), dtype=np.uint8) * 240
        
#         # העתקת תמונת הלוח למרכז
#         board_height, board_width = board_img.shape[:2]
#         if board_img.shape[2] == 4:
#             board_img = board_img[:, :, :3]  # הסרת ערוץ Alpha
        
#         x_offset = (self.new_window_width - board_width) // 2
#         y_offset = (self.new_window_height - board_height) // 2
#         extended_img[y_offset:y_offset + board_height, x_offset:x_offset + board_width] = board_img
        
#         # חישוב מיקום הפאנלים בצד ימין
#         panel_x = x_offset + board_width + 10
#         panel_width = self.ui_panel_width - 20
        
#         # ✨ פאנל ניקוד
#         score_panel_y = 10
#         score_panel_height = 200
#         self.score_system.draw_on_image(extended_img, panel_x, score_panel_y, panel_width, score_panel_height)
        
#         # ✨ פאנל רשימת מהלכים
#         moves_panel_y = score_panel_y + score_panel_height + 20
#         moves_panel_height = 300
#         self.moves_log.draw_on_image(extended_img, panel_x, moves_panel_y, panel_width, moves_panel_height)
        
#         # פאנל פקדים
#         controls_panel_y = moves_panel_y + moves_panel_height + 20
#         self.draw_controls_panel(extended_img, panel_x, controls_panel_y, panel_width, 100)
        
#         # פאנל מידע משחק
#         game_info_y = controls_panel_y + 100 + 20
#         self.draw_game_info_panel(extended_img, panel_x, game_info_y, panel_width, 100)
        
#         return extended_img

#     def draw_controls_panel(self, img, x, y, width, height):
#         """ציור פאנל הפקדים"""
#         # רקע הפאנל
#         cv2.rectangle(img, (x, y), (x + width, y + height), (220, 220, 220), -1)
#         cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
#         # כותרת
#         cv2.putText(img, "Controls", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
#         # הוראות
#         controls = [
#             f"{self.player1_name}: 8246+Enter",
#             f"{self.player2_name}: WASD+Space",
#             "Q/ESC: Exit"
#         ]
        
#         for i, control in enumerate(controls):
#             cv2.putText(img, control, (x + 10, y + 40 + i * 20), 
#                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

#     def draw_game_info_panel(self, img, x, y, width, height):
#         """ציור פאנל מידע המשחק"""
#         # רקע הפאנל
#         cv2.rectangle(img, (x, y), (x + width, y + height), (200, 200, 255), -1)
#         cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
#         # כותרת
#         cv2.putText(img, "Game Status", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
#         # מידע
#         status = "Running" if not self.game_over else f"Game Over - {self.winner} Wins!"
#         cv2.putText(img, f"Status: {status}", (x + 10, y + 45), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
        
#         cv2.putText(img, f"Pieces: {len(self.pieces_data)}", (x + 10, y + 65), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

#     async def listen_to_server(self):
#         """האזנה להודעות מהשרת"""
#         try:
#             async for message in self.websocket:
#                 await self.handle_server_message(message)
#         except websockets.exceptions.ConnectionClosed:
#             print("🔌 Connection to server lost")
#             self.connected = False
#         except Exception as e:
#             print(f"❌ Error listening to server: {e}")
#             self.connected = False

#     def handle_keyboard_opencv(self):
#         """טיפול בקלט מקלדת דרך OpenCV - רץ בthread נפרד"""
#         while self.running:
#             if self.extended_img is not None:
#                 cv2.imshow("Chess Game - Client", self.extended_img)
                
#                 # המתן למקש (30ms timeout)
#                 key = cv2.waitKey(30) & 0xFF
                
#                 if key != 255 and key != -1:  # מקש נלחץ
#                     print(f"🔑 Client captured key: {key}")
                    
#                     # שלח את המקש לשרת באופן אסינכרוני
#                     if self.connected:
#                         loop = asyncio.new_event_loop()
#                         asyncio.set_event_loop(loop)
#                         loop.run_until_complete(self.send_keyboard_input(key))
#                         loop.close()
                    
#                     # בדוק אם צריך לצאת
#                     if key == 27 or key == ord('q'):  # ESC או Q
#                         self.running = False
#                         break
            
#             time.sleep(0.016)  # ~60 FPS

#     def display_loop(self):
#         """לולאת התצוגה - רץ בthread נפרד"""
#         while self.running:
#             # צייר את המשחק
#             img = self.draw_game()
            
#             if img is not None:
#                 self.extended_img = img
            
#             time.sleep(1/60.0)  # 60 FPS

#     async def run(self):
#         """הפעלת הלקוח"""
#         # התחבר לשרת
#         if not await self.connect_to_server():
#             return
        
#         # הפעל threads לתצוגה ולקלט
#         display_thread = threading.Thread(target=self.display_loop, daemon=True)
#         keyboard_thread = threading.Thread(target=self.handle_keyboard_opencv, daemon=True)
        
#         display_thread.start()
#         keyboard_thread.start()
        
#         print("🎮 Client is running with full UI! Use keyboard to play!")
#         print("🎮 הלקוח פועל עם ממשק מלא! השתמש במקלדת כדי לשחק!")
#         print("🏆 Score system enabled!")
#         print("📝 Moves log enabled!")
        
#         # האזן לשרת
#         await self.listen_to_server()
        
#         # נקה משאבים
#         self.running = False
#         cv2.destroyAllWindows()
#         await self.disconnect_from_server()

# async def main():
#     client = ChessClient()
    
#     print("🚀 Starting Enhanced Chess Client...")
#     print("🚀 מפעיל לקוח שחמט משופר...")
    
#     try:
#         await client.run()
#     except KeyboardInterrupt:
#         print("\n🛑 Client stopped by user")
#     except Exception as e:
#         print(f"❌ Client error: {e}")
#     finally:
#         client.running = False
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     asyncio.run(main())
import asyncio
import websockets
import json
import cv2
import numpy as np
import pathlib
import threading
import time
from typing import Dict, List, Optional, Tuple

# Import your existing classes for visualization
from It1_interfaces.img import Img
from It1_interfaces.Board import Board
from It1_interfaces.PieceFactory import PieceFactory

class ChessClient:
    def __init__(self, server_uri: str = "ws://localhost:8765"):
        self.server_uri = server_uri
        self.websocket = None
        self.connected = False
        self.running = True
        
        # Game state from server
        self.pieces_data = []
        self.board_size = (822, 822)
        self.player1_cursor = [0, 7]
        self.player2_cursor = [0, 0]
        self.selected_piece_player1 = None
        self.selected_piece_player2 = None
        self.game_over = False
        self.winner = None
        self.my_player = None  # מספר השחקן שלי (1, 2, או None לצופה)
        
        # נתוני ניקוד ומהלכים
        self.score_data = {}
        self.moves_data = {}
        
        # Display components
        self.board = None
        self.pieces_sprites = {}  # piece_id -> sprite image
        self.extended_img = None
        
        # UI settings (copied from Game.py) - הגדלה לפאנלים הנוספים
        self.ui_panel_width = 400  # הגדלה מ-300 ל-400 לפאנלים הרחבים יותר
        self.new_window_width = 822 + self.ui_panel_width + 800
        self.new_window_height = max(822, 600) + 200
        
        self.initialize_display()

    def initialize_display(self):
        """אתחול רכיבי התצוגה"""
        print("📸 Loading board image for client...")
        
        # טען את תמונת הלוח (בדיוק כמו במain.py)
        img = Img()
        img.read(str("C:/Users/board.png"), size=(822, 822))
        
        if img.img is None:
            raise RuntimeError("Board image failed to load in client!")
        
        # צור את הלוח
        self.board = Board(
            cell_H_pix=103.5,
            cell_W_pix=102.75,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=img
        )
        
        # טען sprites של הכלים
        self.load_piece_sprites()
        
        print("🖼️ Display initialized successfully!")

    def load_piece_sprites(self):
        """טען את sprites של כל הכלים"""
        pieces_root = pathlib.Path(r"C:\Users\pieces")
        piece_types = ["RB", "NB", "BB", "QB", "KB", "PB", "RW", "NW", "BW", "QW", "KW", "PW"]
        
        for piece_type in piece_types:
            try:
                # טען sprite מתיקיית idle
                sprite_path = pieces_root / piece_type / "states" / "idle" / "sprites"
                if sprite_path.exists():
                    # קח את התמונה הראשונה
                    sprite_files = list(sprite_path.glob("*.png"))
                    if sprite_files:
                        sprite_img = Img()
                        sprite_img.read(str(sprite_files[0]), size=(80, 80))
                        if sprite_img.img is not None:
                            self.pieces_sprites[piece_type] = sprite_img
                            print(f"✅ Loaded sprite for {piece_type}")
                        else:
                            print(f"❌ Failed to load sprite for {piece_type}")
            except Exception as e:
                print(f"❌ Error loading sprite for {piece_type}: {e}")

    async def connect_to_server(self):
        """התחברות לשרת"""
        try:
            print(f"🔌 Connecting to server at {self.server_uri}...")
            self.websocket = await websockets.connect(self.server_uri)
            self.connected = True
            print("✅ Connected to server!")
            
            # בקש מצב משחק ראשוני
            await self.request_game_state()
            
            return True
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False

    async def disconnect_from_server(self):
        """התנתקות מהשרת"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("🔌 Disconnected from server")

    async def send_keyboard_input(self, key: int):
        """שליחת קלט מקלדת לשרת"""
        if not self.connected or not self.websocket:
            return
            
        message = {
            'type': 'keyboard_input',
            'key': key
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"⌨️ Sent key {key} to server")
        except Exception as e:
            print(f"❌ Error sending keyboard input: {e}")

    async def request_game_state(self):
        """בקשת מצב המשחק מהשרת"""
        if not self.connected or not self.websocket:
            return
            
        message = {'type': 'get_game_state'}
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"❌ Error requesting game state: {e}")

    async def handle_server_message(self, message: str):
        """טיפול בהודעות מהשרת"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'game_state':
                self.update_game_state(data.get('data', {}))
            elif msg_type == 'pong':
                print("🏓 Received pong from server")
            else:
                print(f"❓ Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON from server: {message}")
        except Exception as e:
            print(f"❌ Error handling server message: {e}")

    def update_game_state(self, game_data: Dict):
        """עדכון מצב המשחק מנתוני השרת"""
        self.pieces_data = game_data.get('pieces', [])
        self.board_size = tuple(game_data.get('board_size', (822, 822)))
        self.player1_cursor = game_data.get('player1_cursor', [0, 7])
        self.player2_cursor = game_data.get('player2_cursor', [0, 0])
        self.selected_piece_player1 = game_data.get('selected_piece_player1')
        self.selected_piece_player2 = game_data.get('selected_piece_player2')
        self.game_over = game_data.get('game_over', False)
        self.winner = game_data.get('winner')
        
        # עדכון נתוני ניקוד ומהלכים
        self.score_data = game_data.get('score_data', {})
        self.moves_data = game_data.get('moves_data', {})
        
        # מידע על השחקן
        new_player = game_data.get('your_player')
        if new_player != self.my_player:
            self.my_player = new_player
            if self.my_player == 1:
                print("🎮 You are Player 1 - White pieces (Controls: Numpad 8246, Enter/5/0)")
            elif self.my_player == 2:
                print("🎮 You are Player 2 - Black pieces (Controls: WASD, Space)")
            else:
                print("👁️ You are a spectator - You can watch but not play")
        
        # אם המשחק נגמר, הצג הודעת ניצחון
        if self.game_over and self.winner:
            print(f"🏆 Game Over! Winner: {self.winner}")

    def draw_game(self):
        """ציור המשחק - מבוסס על Game._draw()"""
        if not self.board:
            return None
            
        # צור עותק נקי של הלוח
        display_board = self.board.clone()
        
        # ציור כל הכלים על העותק
        self.draw_pieces_on_board(display_board)
        
        # ציור סמנים של השחקנים
        self.draw_cursors(display_board)
        
        # יצירת תמונה מורחבת עם פאנלים
        if hasattr(display_board, "img"):
            board_img = display_board.img.img
            
            # יצירת תמונה חדשה גדולה יותר
            self.extended_img = self.create_extended_display(board_img)
            
            return self.extended_img
        
        return None

    def draw_pieces_on_board(self, board):
        """ציור הכלים על הלוח לפי מיקומי הפיקסלים מהשרת"""
        for piece_data in self.pieces_data:
            piece_id = piece_data['id']
            pixel_pos = piece_data.get('pixel_position', (0, 0))
            
            # חלץ את סוג הכלי מה-ID (למשל "PW0" -> "PW")
            piece_type = ''.join([c for c in piece_id if not c.isdigit()])
            
            # מצא את ה-sprite המתאים
            sprite = self.pieces_sprites.get(piece_type)
            if sprite and sprite.img is not None:
                x, y = pixel_pos
                sprite.draw_on(board.img, int(x), int(y))

    def draw_cursors(self, board):
        """ציור הסמנים - מועתק מ-Game._draw_cursors()"""
        if hasattr(board, 'img') and hasattr(board.img, 'img'):
            img = board.img.img
            
            # חישוב גודל משבצת
            board_height, board_width = img.shape[:2]
            cell_width = board_width // 8
            cell_height = board_height // 8
            
            # ציור סמן שחקן 1 (כחול עבה) - רק אם זה השחקן הנוכחי
            x1, y1 = self.player1_cursor
            top_left_1 = (x1 * cell_width, y1 * cell_height)
            bottom_right_1 = ((x1 + 1) * cell_width - 1, (y1 + 1) * cell_height - 1)
            if self.my_player == 1:
                cv2.rectangle(img, top_left_1, bottom_right_1, (255, 0, 0), 8)  # כחול BGR
            
            # ציור סמן שחקן 2 (אדום עבה) - רק אם זה השחקן הנוכחי
            x2, y2 = self.player2_cursor
            top_left_2 = (x2 * cell_width, y2 * cell_height)
            bottom_right_2 = ((x2 + 1) * cell_width - 1, (y2 + 1) * cell_height - 1)
            if self.my_player == 2:
                cv2.rectangle(img, top_left_2, bottom_right_2, (0, 0, 255), 8)  # אדום BGR
            
            # סימון כלי נבחר
            if self.selected_piece_player1:
                piece_pos = self.get_piece_position_by_id(self.selected_piece_player1)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 0), 4)  # ירוק עבה
            
            if self.selected_piece_player2:
                piece_pos = self.get_piece_position_by_id(self.selected_piece_player2)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 255), 4)  # צהוב עבה

    def get_piece_position_by_id(self, piece_id: str) -> Optional[Tuple[int, int]]:
        """מצא מיקום כלי לפי ID"""
        for piece_data in self.pieces_data:
            if piece_data['id'] == piece_id:
                return tuple(piece_data.get('position', (0, 0)))
        return None

    def create_extended_display(self, board_img):
        """יצירת תצוגה מורחבת עם פאנלי ניקוד ומהלכים"""
        import numpy as np
        
        # יצירת תמונה חדשה עם גודל מורחב
        extended_img = np.ones((self.new_window_height, self.new_window_width, 3), dtype=np.uint8) * 240
        
        # העתקת תמונת הלוח למרכז
        board_height, board_width = board_img.shape[:2]
        if board_img.shape[2] == 4:
            board_img = board_img[:, :, :3]  # הסרת ערוץ Alpha
        
        x_offset = (self.new_window_width - board_width) // 2
        y_offset = (self.new_window_height - board_height) // 2
        extended_img[y_offset:y_offset + board_height, x_offset:x_offset + board_width] = board_img
        
        # חישוב מיקום הפאנלים בצד ימין
        panel_x = x_offset + board_width + 20
        panel_width = self.ui_panel_width - 40
        
        # פאנל ניקוד
        score_panel_y = 20
        score_panel_height = 200
        self.draw_score_panel(extended_img, panel_x, score_panel_y, panel_width, score_panel_height)
        
        # פאנל רשימת מהלכים
        moves_panel_y = score_panel_y + score_panel_height + 20
        moves_panel_height = 300
        self.draw_moves_panel(extended_img, panel_x, moves_panel_y, panel_width, moves_panel_height)
        
        # פאנל פקדים
        controls_panel_y = moves_panel_y + moves_panel_height + 20
        self.draw_controls_panel(extended_img, panel_x, controls_panel_y, panel_width, 120)
        
        # פאנל מידע המשחק
        game_info_panel_y = controls_panel_y + 140
        self.draw_game_info_panel(extended_img, panel_x, game_info_panel_y, panel_width, 100)
        
        return extended_img

    def draw_score_panel(self, img, x, y, width, height):
        """ציור פאנל הניקוד - מבוסס על ScoreSystem"""
        # רקע הפאנל
        cv2.rectangle(img, (x, y), (x + width, y + height), (220, 255, 220), -1)  # רקע ירוק בהיר
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # כותרת
        cv2.putText(img, "Score Board", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        if self.score_data:
            player1_name = self.score_data.get('player1_name', 'Player 1')
            player2_name = self.score_data.get('player2_name', 'Player 2')
            player1_score = self.score_data.get('player1_score', 0)
            player2_score = self.score_data.get('player2_score', 0)
            
            # ציון שחקן 1 (לבן)
            player1_color = (0, 0, 255) if self.my_player == 1 else (0, 0, 0)  # אדום אם זה השחקן הנוכחי
            cv2.putText(img, f"{player1_name} (White):", (x + 10, y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, player1_color, 2 if self.my_player == 1 else 1)
            cv2.putText(img, f"Score: {player1_score}", (x + 10, y + 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, player1_color, 2 if self.my_player == 1 else 1)
            
            # ציון שחקן 2 (שחור)
            player2_color = (255, 0, 0) if self.my_player == 2 else (0, 0, 0)  # כחול אם זה השחקן הנוכחי
            cv2.putText(img, f"{player2_name} (Black):", (x + 10, y + 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, player2_color, 2 if self.my_player == 2 else 1)
            cv2.putText(img, f"Score: {player2_score}", (x + 10, y + 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, player2_color, 2 if self.my_player == 2 else 1)
            
            # הצגת כלים שנתפסו (אם יש)
            player1_captures = self.score_data.get('player1_captures', [])
            player2_captures = self.score_data.get('player2_captures', [])
            
            if player1_captures:
                captured_str = ", ".join(player1_captures[-5:])  # 5 אחרונים
                cv2.putText(img, f"Captured: {captured_str}", (x + 10, y + 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, player1_color, 1)
            
            if player2_captures:
                captured_str = ", ".join(player2_captures[-5:])  # 5 אחרונים
                cv2.putText(img, f"Captured: {captured_str}", (x + 10, y + 180), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, player2_color, 1)
        else:
            cv2.putText(img, "Waiting for score data...", (x + 10, y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)

    def draw_moves_panel(self, img, x, y, width, height):
        """ציור פאנל המהלכים - מבוסס על MovesLog"""
        # רקע הפאנל
        cv2.rectangle(img, (x, y), (x + width, y + height), (255, 255, 220), -1)  # רקע צהוב בהיר
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # כותרת
        cv2.putText(img, "Moves Log", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        if self.moves_data and 'moves_list' in self.moves_data:
            moves_list = self.moves_data['moves_list']
            move_count = self.moves_data.get('move_count', 0)
            
            cv2.putText(img, f"Total moves: {move_count}", (x + 10, y + 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            
            # הצג רק מהלכים של השחקן הנוכחי אם זה לא צופה
            if self.my_player is not None:
                # סנן מהלכים לפי השחקן
                if self.my_player == 1:
                    # שחקן 1 - כלים לבנים (מכילים W)
                    filtered_moves = [move for move in moves_list if 'W' in move.get('piece_id', '')]
                    title_suffix = " (Your moves - White)"
                elif self.my_player == 2:
                    # שחקן 2 - כלים שחורים (מכילים B)
                    filtered_moves = [move for move in moves_list if 'B' in move.get('piece_id', '')]
                    title_suffix = " (Your moves - Black)"
            else:
                filtered_moves = moves_list
                title_suffix = " (All moves)"
            
            # הצג כותרת משנה
            cv2.putText(img, title_suffix, (x + 10, y + 65), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            
            # הצג עד 10 מהלכים אחרונים
            display_moves = filtered_moves[-10:] if len(filtered_moves) > 10 else filtered_moves
            
            for i, move in enumerate(display_moves):
                move_text = f"{i+1}. {move.get('piece_id', 'Unknown')}: {move.get('description', 'Move')}"
                if len(move_text) > 35:  # קצר טקסט ארוך
                    move_text = move_text[:32] + "..."
                
                # צבע שונה לפי סוג הכלי
                color = (0, 0, 255) if 'W' in move.get('piece_id', '') else (255, 0, 0)  # אדום ללבן, כחול לשחור
                if self.my_player is None:  # צופה רואה הכל בשחור
                    color = (0, 0, 0)
                    
                cv2.putText(img, move_text, (x + 10, y + 85 + i * 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        else:
            cv2.putText(img, "No moves yet...", (x + 10, y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)

    def draw_controls_panel(self, img, x, y, width, height):
        """ציור פאנל הפקדים"""
        # רקע הפאנל
        cv2.rectangle(img, (x, y), (x + width, y + height), (220, 220, 220), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # כותרת
        cv2.putText(img, "Controls", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # מידע על השחקן
        if self.my_player == 1:
            player_text = "You: Player 1 (White)"
            controls = [
                "Movement: 8(up) 2(down)",
                "          4(left) 6(right)",
                "Select: Enter/5/0",
                "Exit: Q/ESC"
            ]
            color = (0, 0, 255)  # אדום
        elif self.my_player == 2:
            player_text = "You: Player 2 (Black)"
            controls = [
                "Movement: W(up) S(down)",
                "          A(left) D(right)",
                "Select: Space",
                "Exit: Q/ESC"
            ]
            color = (255, 0, 0)  # כחול
        else:
            player_text = "You: Spectator"
            controls = [
                "You can only watch",
                "Exit: Q/ESC"
            ]
            color = (128, 128, 128)  # אפור
        
        # הצג מידע שחקן
        cv2.putText(img, player_text, (x + 10, y + 45), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # הוראות פקדים
        for i, control in enumerate(controls):
            cv2.putText(img, control, (x + 10, y + 70 + i * 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

    def draw_game_info_panel(self, img, x, y, width, height):
        """ציור פאנל מידע המשחק"""
        # רקע הפאנל
        cv2.rectangle(img, (x, y), (x + width, y + height), (200, 200, 255), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (0, 0, 0), 2)
        
        # כותרת
        cv2.putText(img, "Game Status", (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # מידע
        if self.game_over:
            status = f"Game Over - {self.winner} Wins!" if self.winner else "Game Over"
            status_color = (0, 0, 255) if self.winner else (0, 0, 0)
        else:
            status = "Game Running"
            status_color = (0, 128, 0)
            
        cv2.putText(img, f"Status: {status}", (x + 10, y + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, status_color, 1)
        
        cv2.putText(img, f"Pieces on board: {len(self.pieces_data)}", (x + 10, y + 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
        
        # מיקום סמנים רק עבור השחקן הנוכחי
        if self.my_player == 1:
            cv2.putText(img, f"Your cursor: {self.player1_cursor}", (x + 10, y + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
        elif self.my_player == 2:
            cv2.putText(img, f"Your cursor: {self.player2_cursor}", (x + 10, y + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

    def is_valid_key_for_player(self, key: int) -> bool:
        """בדוק אם המקש תקין עבור השחקן הנוכחי"""
        if self.my_player is None:  # צופה
            return key == 27 or key == ord('q')  # רק יציאה
        
        char = None
        if 32 <= key <= 126:
            char = chr(key).lower()
        
        # תמיכה במקלדת עברית
        hebrew_keys = {
            ord('\''): 'w',
            ord('ש'): 'a', 
            ord('ד'): 's',
            ord('ג'): 'd'
        }
        detected_hebrew = hebrew_keys.get(key)
        
        if self.my_player == 1:  # שחקן 1 - מקשי מספרים
            return (key in [50, 52, 53, 54, 56, 48] or  # 2,4,5,6,8,0
                    char in ['2', '4', '5', '6', '8', '0'] or
                    key in [13, 10, 39, 226, 249] or  # Enter
                    key == 27 or key == ord('q'))  # יציאה
        
        elif self.my_player == 2:  # שחקן 2 - WASD
            return (key in [119, 87, 115, 83, 97, 65, 100, 68, 32] or  # W,S,A,D,Space
                    char in ['w', 's', 'a', 'd', ' '] or
                    detected_hebrew in ['w', 's', 'a', 'd'] or
                    key in [1493, 215, 246, 1500, 1491, 212, 213, 1504, 
                           1513, 249, 251, 1506, 1499, 235, 237, 1507] or  # עברית
                    key == 27 or key == ord('q'))  # יציאה
        
        return False

    async def listen_to_server(self):
        """האזנה להודעות מהשרת"""
        try:
            async for message in self.websocket:
                await self.handle_server_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection to server lost")
            self.connected = False
        except Exception as e:
            print(f"❌ Error listening to server: {e}")
            self.connected = False

    def handle_keyboard_opencv(self):
        """טיפול בקלט מקלדת דרך OpenCV - רץ בthread נפרד"""
        while self.running:
            if self.extended_img is not None:
                cv2.imshow("Chess Game - Client", self.extended_img)
                
                # המתן למקש (30ms timeout)
                key = cv2.waitKey(30) & 0xFF
                
                if key != 255 and key != -1:  # מקש נלחץ
                    print(f"🔑 Client captured key: {key}")
                    
                    # בדוק אם המקש תקין עבור השחקן
                    if self.is_valid_key_for_player(key):
                        # שלח את המקש לשרת באופן אסינכרוני
                        if self.connected:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.send_keyboard_input(key))
                            loop.close()
                    else:
                        if self.my_player == 1:
                            print("🚫 Invalid key for Player 1. Use numpad: 8246, Enter/5/0")
                        elif self.my_player == 2:
                            print("🚫 Invalid key for Player 2. Use WASD, Space")
                        else:
                            print("🚫 You are a spectator - you cannot control pieces")
                    
                    # בדוק אם צריך לצאת
                    if key == 27 or key == ord('q'):  # ESC או Q
                        self.running = False
                        break
            
            time.sleep(0.016)  # ~60 FPS

    def display_loop(self):
        """לולאת התצוגה - רץ בthread נפרד"""
        while self.running:
            # צייר את המשחק
            img = self.draw_game()
            
            if img is not None:
                self.extended_img = img
            
            time.sleep(1/60.0)  # 60 FPS

    async def run(self):
        """הפעלת הלקוח"""
        # התחבר לשרת
        if not await self.connect_to_server():
            return
        
        # הפעל threads לתצוגה ולקלט
        display_thread = threading.Thread(target=self.display_loop, daemon=True)
        keyboard_thread = threading.Thread(target=self.handle_keyboard_opencv, daemon=True)
        
        display_thread.start()
        keyboard_thread.start()
        
        print("🎮 Client is running with Score & Moves tracking!")
        print("🎮 הלקוח פועל עם מעקב אחר ניקוד ומהלכים!")
        print("🏆 Each player sees only their own moves and score")
        
        # האזן לשרת
        await self.listen_to_server()
        
        # נקה משאבים
        self.running = False
        cv2.destroyAllWindows()
        await self.disconnect_from_server()

async def main():
    client = ChessClient()
    
    print("🚀 Starting Chess Client...")
    print("🚀 מפעיל לקוח שחמט...")
    print("🎮 Connecting as new player or spectator...")
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n🛑 Client stopped by user")
    except Exception as e:
        print(f"❌ Client error: {e}")
    finally:
        client.running = False
        cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())