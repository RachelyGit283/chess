# import asyncio
# import websockets
# import json
# import pathlib
# import time
# from typing import Dict, List, Optional
# from dataclasses import dataclass

# # Import your existing classes
# from It1_interfaces.img import Img
# from It1_interfaces.Board import Board
# from It1_interfaces.Game import Game
# from It1_interfaces.PieceFactory import PieceFactory
# from It1_interfaces.Command import Command

# # ✨ ייבוא מערכת האירועים
# from It1_interfaces.EventSystem import Event, EventType, event_publisher
# import queue

# @dataclass
# class GameState:
#     """מחלקה לשמירת מצב המשחק"""
#     pieces_data: List[Dict]
#     board_size: tuple
#     player1_cursor: List[int]
#     player2_cursor: List[int]
#     selected_piece_player1: Optional[str]
#     selected_piece_player2: Optional[str]
#     game_over: bool
#     winner: Optional[str]

# class ChessServer:
#     def __init__(self):
#         self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}  # client_id -> websocket
#         self.game: Optional[Game] = None
#         self.game_initialized = False
        
#         # ✨ הרשמה לאירועי המערכת
#         self.setup_event_listeners()
        
#     def setup_event_listeners(self):
#         """הגדרת מאזינים לאירועי המשחק"""
#         def on_piece_captured(event_data):
#             asyncio.create_task(self.broadcast_game_event('PIECE_CAPTURED', event_data))
            
#         def on_move_made(event_data):
#             asyncio.create_task(self.broadcast_game_event('MOVE_MADE', event_data))
            
#         def on_pawn_promoted(event_data):
#             asyncio.create_task(self.broadcast_game_event('PAWN_PROMOTED', event_data))
            
#         def on_king_captured(event_data):
#             asyncio.create_task(self.broadcast_game_event('KING_CAPTURED', event_data))
        
#         def on_game_start(event_data):
#             asyncio.create_task(self.broadcast_game_event('GAME_START', event_data))
        
#         # רישום המאזינים
#         event_publisher.subscribe(EventType.PIECE_CAPTURED, on_piece_captured)
#         event_publisher.subscribe(EventType.MOVE_MADE, on_move_made)
#         event_publisher.subscribe(EventType.PAWN_PROMOTED, on_pawn_promoted)
#         event_publisher.subscribe(EventType.KING_CAPTURED, on_king_captured)
#         event_publisher.subscribe(EventType.GAME_START, on_game_start)
        
#         print("🎧 Event listeners registered!")

#     async def register_client(self, websocket, client_id: str):
#         """רישום לקוח חדש"""
#         self.clients[client_id] = websocket
#         print(f"🔌 Client {client_id} connected. Total clients: {len(self.clients)}")
        
#         # אם זהו הלקוח הראשון, אתחל את המשחק
#         if len(self.clients) == 1 and not self.game_initialized:
#             await self.initialize_game()
        
#         # שלח מצב המשחק הנוכחי ללקוח החדש
#         if self.game:
#             await self.send_game_state(websocket)

#     async def unregister_client(self, websocket, client_id: str):
#         """ביטול רישום לקוח"""
#         if client_id in self.clients:
#             del self.clients[client_id]
#         print(f"🔌 Client {client_id} disconnected. Total clients: {len(self.clients)}")

#     async def broadcast_game_event(self, event_type: str, event_data: dict):
#         """שידור אירוע משחק לכל הלקוחות"""
#         if not self.clients:
#             return
            
#         message = {
#             'type': 'game_event',
#             'event': {
#                 'type': event_type,
#                 'data': event_data
#             }
#         }
        
#         # שלח לכל הלקוחות המחוברים
#         disconnected_clients = []
#         for client_id, websocket in self.clients.items():
#             try:
#                 await websocket.send(json.dumps(message))
#                 print(f"📡 Sent {event_type} event to {client_id}")
#             except websockets.exceptions.ConnectionClosed:
#                 disconnected_clients.append(client_id)
        
#         # הסר לקוחות מנותקים
#         for client_id in disconnected_clients:
#             del self.clients[client_id]

#     async def initialize_game(self):
#         """אתחול המשחק - בדיוק כמו במain.py"""
#         print("🎮 Starting chess game on server...")
#         print("🎮 מתחיל משחק שחמט בשרת...")

#         # טען את התמונה
#         print("📸 Loading board image...")
#         img = Img()
#         img_path = pathlib.Path(__file__).parent.parent / "board.png"
#         img.read(str("C:/Users/board.png"), size=(822, 822))
        
#         print("📸 Image loaded:", img.img is not None)
#         if img.img is None:
#             raise RuntimeError("Board image failed to load!")

#         # צור את הלוח עם התמונה
#         board = Board(
#             cell_H_pix=103.5,
#             cell_W_pix=102.75,
#             cell_H_m=1,
#             cell_W_m=1,
#             W_cells=8,
#             H_cells=8,
#             img=img
#         )
        
#         pieces_root = pathlib.Path(r"C:\Users\pieces")
#         factory = PieceFactory(board, pieces_root)

#         start_positions = [
#             # כלים שחורים בחלק העליון של הלוח (שורות 0-1)
#             ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB", (3, 0)), ("KB", (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
#             ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
#             # כלים לבנים בחלק התחתון של הלוח (שורות 6-7)
#             ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
#             ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW", (3, 7)), ("KW", (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
#         ]

#         pieces = []
#         piece_counters = {}  # Track count per piece type for unique IDs

#         # צור את המשחק עם התור
#         self.game = Game([], board)

#         for p_type, cell in start_positions:
#             try:
#                 # Create unique piece ID by adding counter
#                 if p_type not in piece_counters:
#                     piece_counters[p_type] = 0
#                 unique_id = f"{p_type}{piece_counters[p_type]}"
#                 piece_counters[p_type] += 1
#                 piece = factory.create_piece(p_type, cell, self.game.user_input_queue)
#                 # Override the piece ID with unique ID
#                 piece.piece_id = unique_id
#                 # Update physics with the correct piece_id
#                 piece._state._physics.piece_id = unique_id
#                 pieces.append(piece)
#             except Exception as e:
#                 print(f"בעיה עם {p_type}: {e}")

#         # עדכן את המשחק עם הכלים
#         self.game.pieces = pieces
#         self.game_initialized = True
#         print(f"🎮 Game initialized with {len(pieces)} pieces")
        
#         # התחל את הלולאה העיקרית של המשחק
#         asyncio.create_task(self.game_loop())

#     async def game_loop(self):
#         """לולאת המשחק העיקרית"""
#         if not self.game:
#             return
            
#         start_ms = int(time.monotonic() * 1000)
#         for p in self.game.pieces:
#             p.reset(start_ms)

#         print("🎮 Starting game loop...")
        
#         while not self.game.game_over:
#             now = int(time.monotonic() * 1000)

#             # (1) update physics & animations
#             for p in self.game.pieces:
#                 p.update(now)

#             # (2) update new systems
#             self.game.message_overlay.update(now / 1000.0)

#             # (3) handle queued Commands
#             while not self.game.user_input_queue.empty():
#                 print("📥 יש קומנד בתור!")
#                 cmd: Command = self.game.user_input_queue.get()
#                 print("📥 cmd:", cmd)
#                 self.game._process_input(cmd)
                
#                 # שלח עדכון ללקוחות אחרי עיבוד הקומנד
#                 await self.broadcast_game_state()
                
#                 if self.game.game_over:
#                     break

#             # (4) detect captures
#             self.game._resolve_collisions()
            
#             # (5) שלח עדכון מחזורי ללקוחות
#             await self.broadcast_game_state()
            
#             # (6) שליטה בקצב פריימים - 60 FPS
#             await asyncio.sleep(1/60.0)

#         print("🎮 Game loop ended")

#     async def handle_client_message(self, websocket, message: str, client_id: str):
#         """טיפול בהודעות מהלקוחות"""
#         try:
#             data = json.loads(message)
#             msg_type = data.get('type')
            
#             if msg_type == 'keyboard_input':
#                 # טיפול בקלט מקלדת
#                 key = data.get('key')
#                 await self.handle_keyboard_input(key, client_id)
                
#             elif msg_type == 'get_game_state':
#                 # בקשה למצב המשחק
#                 await self.send_game_state(websocket)
                
#             elif msg_type == 'ping':
#                 # בדיקת חיבור
#                 await websocket.send(json.dumps({'type': 'pong'}))
                
#         except json.JSONDecodeError:
#             print(f"❌ Invalid JSON from client {client_id}: {message}")
#         except Exception as e:
#             print(f"❌ Error handling message from client {client_id}: {e}")

#     async def handle_keyboard_input(self, key: int, client_id: str):
#         """טיפול בקלט מקלדת - העתקה מ-Game._handle_keyboard_input"""
#         if not self.game:
#             return
            
#         print(f"\n=== KEY PRESSED by {client_id}: {key} ===")
#         if 32 <= key <= 126:
#             print(f"Character: '{chr(key)}'")
#         else:
#             print(f"Special key code: {key}")
        
#         # Check for exit keys first
#         if key == 27 or key == ord('q'):  # ESC או Q
#             self.game.game_over = True
#             await self.broadcast_game_state()
#             return
        
#         # Convert to character for easier handling
#         char = None
#         if 32 <= key <= 126:
#             char = chr(key).lower()
        
#         # תמיכה מלאה במקלדת עברית
#         hebrew_keys = {
#             ord('\''): 'w',
#             ord('ש'): 'a',
#             ord('ד'): 's',
#             ord('ג'): 'd'
#         }
#         detected_hebrew = hebrew_keys.get(key)
#         if detected_hebrew:
#             print(f"🔥 זוהה מקש עברי: {key} -> {detected_hebrew}")
#             char = detected_hebrew
        
#         # Player 2 controls - WASD (שחקן 2 שולט בכלים שחורים)
#         wasd_detected = False
        
#         if (key in [119, 87] or char == 'w' or 
#             key in [1493, 215, 246, 1500] or detected_hebrew == 'w'):
#             print("🔥 Player 2: Moving UP (W/ו)")
#             self.game._move_cursor_player2(0, -1)
#             wasd_detected = True
#         elif (key in [115, 83] or char == 's' or 
#               key in [1491, 212, 213, 1504] or detected_hebrew == 's'):
#             print("🔥 Player 2: Moving DOWN (S/ד)")
#             self.game._move_cursor_player2(0, 1)
#             wasd_detected = True
#         elif (key in [97, 65] or char == 'a' or 
#               key in [1513, 249, 251, 1506] or detected_hebrew == 'a'):
#             print("🔥 Player 2: Moving LEFT (A/ש)")
#             self.game._move_cursor_player2(-1, 0)
#             wasd_detected = True
#         elif (key in [100, 68] or char == 'd' or 
#               key in [1499, 235, 237, 1507] or detected_hebrew == 'd'):
#             print("🔥 Player 2: Moving RIGHT (D/כ)")
#             self.game._move_cursor_player2(1, 0)
#             wasd_detected = True
#         elif key == 32 or char == ' ':  # Space
#             print("🔥 Player 2: Selecting piece (SPACE)")
#             self.game._select_piece_player2()
#             wasd_detected = True
        
#         # Player 1 controls - מקשי מספרים (שחקן 1 שולט בכלים לבנים)
#         elif key == 56 or char == '8':  # 8 key
#             print("⚡ Player 1: Moving UP (8)")
#             self.game._move_cursor_player1(0, -1)
#         elif key == 50 or char == '2':  # 2 key
#             print("⚡ Player 1: Moving DOWN (2)")
#             self.game._move_cursor_player1(0, 1)
#         elif key == 52 or char == '4':  # 4 key
#             print("⚡ Player 1: Moving LEFT (4)")
#             self.game._move_cursor_player1(-1, 0)
#         elif key == 54 or char == '6':  # 6 key
#             print("⚡ Player 1: Moving RIGHT (6)")
#             self.game._move_cursor_player1(1, 0)
#         elif key == 53 or key == 48 or char == '5' or char == '0':  # 5 or 0 key
#             print("⚡ Player 1: Selecting piece (5 or 0)")
#             self.game._select_piece_player1()
#         elif key in [13, 10, 39, 226, 249]:  # Enter
#             print(f"⚡ Player 1: Selecting piece (Enter code: {key})")
#             self.game._select_piece_player1()
        
#         else:
#             if not wasd_detected:
#                 print(f"❓ Unknown key: {key}")

#         print("=== KEY PROCESSING COMPLETE ===\n")

#     def get_game_state(self) -> GameState:
#         """קבלת מצב המשחק הנוכחי"""
#         if not self.game:
#             return None
            
#         pieces_data = []
#         for piece in self.game.pieces:
#             piece_pos = self.game._get_piece_position(piece)
#             pixel_pos = getattr(piece._state._physics, 'pixel_pos', (0, 0))
            
#             pieces_data.append({
#                 'id': piece.piece_id,
#                 'position': piece_pos,
#                 'pixel_position': pixel_pos,
#                 'moving': getattr(piece._state._physics, 'moving', False)
#             })
        
#         return GameState(
#             pieces_data=pieces_data,
#             board_size=(self.game.board.img.img.shape[1], self.game.board.img.img.shape[0]),
#             player1_cursor=self.game.cursor_pos_player1,
#             player2_cursor=self.game.cursor_pos_player2,
#             selected_piece_player1=self.game.selected_piece_player1.piece_id if self.game.selected_piece_player1 else None,
#             selected_piece_player2=self.game.selected_piece_player2.piece_id if self.game.selected_piece_player2 else None,
#             game_over=self.game.game_over,
#             winner=getattr(self.game, 'winner', None)
#         )

#     async def send_game_state(self, websocket):
#         """שליחת מצב המשחק ללקוח ספציפי"""
#         game_state = self.get_game_state()
#         if game_state:
#             message = {
#                 'type': 'game_state',
#                 'data': {
#                     'pieces': game_state.pieces_data,
#                     'board_size': game_state.board_size,
#                     'player1_cursor': game_state.player1_cursor,
#                     'player2_cursor': game_state.player2_cursor,
#                     'selected_piece_player1': game_state.selected_piece_player1,
#                     'selected_piece_player2': game_state.selected_piece_player2,
#                     'game_over': game_state.game_over,
#                     'winner': game_state.winner
#                 }
#             }
#             try:
#                 await websocket.send(json.dumps(message))
#             except websockets.exceptions.ConnectionClosed:
#                 pass  # הלקוח התנתק

#     async def broadcast_game_state(self):
#         """שידור מצב המשחק לכל הלקוחות"""
#         if not self.clients:
#             return
            
#         game_state = self.get_game_state()
#         if not game_state:
#             return
            
#         message = {
#             'type': 'game_state',
#             'data': {
#                 'pieces': game_state.pieces_data,
#                 'board_size': game_state.board_size,
#                 'player1_cursor': game_state.player1_cursor,
#                 'player2_cursor': game_state.player2_cursor,
#                 'selected_piece_player1': game_state.selected_piece_player1,
#                 'selected_piece_player2': game_state.selected_piece_player2,
#                 'game_over': game_state.game_over,
#                 'winner': game_state.winner
#             }
#         }
        
#         # שלח לכל הלקוחות המחוברים
#         disconnected_clients = []
#         for client_id, websocket in self.clients.items():
#             try:
#                 await websocket.send(json.dumps(message))
#             except websockets.exceptions.ConnectionClosed:
#                 disconnected_clients.append(client_id)
        
#         # הסר לקוחות מנותקים
#         for client_id in disconnected_clients:
#             del self.clients[client_id]

#     async def handle_client(self, websocket):
#         """טיפול בלקוח חדש"""
#         client_id = f"client_{len(self.clients) + 1}"
#         await self.register_client(websocket, client_id)
        
#         try:
#             async for message in websocket:
#                 await self.handle_client_message(websocket, message, client_id)
#         except websockets.exceptions.ConnectionClosed:
#             pass
#         finally:
#             await self.unregister_client(websocket, client_id)

# async def main():
#     server = ChessServer()
    
#     async with websockets.serve(server.handle_client, "localhost", 8765):
#         print("🎮 Enhanced Chess server started on ws://localhost:8765")
#         print("🎧 Event system enabled - clients will receive game events!")
#         print("📡 Broadcasting: captures, moves, promotions, and more!")
#         await asyncio.Future()  # רץ לנצח

# if __name__ == "__main__":
#     asyncio.run(main())





































































































































import asyncio
import websockets
import json
import pathlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
import websockets
import json
import cv2
import numpy as np
import base64
# Import your existing classes
from It1_interfaces.img import Img
from It1_interfaces.Board import Board
from It1_interfaces.Game import Game
from It1_interfaces.PieceFactory import PieceFactory
from It1_interfaces.Command import Command
import queue

@dataclass
class GameState:
    """מחלקה לשמירת מצב המשחק"""
    pieces_data: List[Dict]
    board_size: tuple
    player1_cursor: List[int]
    player2_cursor: List[int]
    selected_piece_player1: Optional[str]
    selected_piece_player2: Optional[str]
    game_over: bool
    winner: Optional[str]
    # הוספת נתוני ניקוד ומהלכים
    score_data: Dict
    moves_data: Dict
    ##למחוק אם לא עובד התמונה
    # extended_img_base64: Optional[str] = None
    
@dataclass
class ClientInfo:
    """מידע על לקוח"""
    websocket: websockets.WebSocketServerProtocol
    player_number: Optional[int]  # 1 או 2, None אם צופה
    client_id: str

class ChessServer:
    def __init__(self):
        self.clients: Dict[str, ClientInfo] = {}  # client_id -> ClientInfo
        self.game: Optional[Game] = None
        self.game_initialized = False
        self.player1_assigned = False
        self.player2_assigned = False
        
    async def register_client(self, websocket, client_id: str):
        """רישום לקוח חדש"""
        # קבע איזה שחקן הוא (1, 2, או צופה)
        player_number = None
        if not self.player1_assigned:
            player_number = 1
            self.player1_assigned = True
            print(f"🎮 Client {client_id} assigned as Player 1 (White pieces)")
        elif not self.player2_assigned:
            player_number = 2
            self.player2_assigned = True
            print(f"🎮 Client {client_id} assigned as Player 2 (Black pieces)")
        else:
            print(f"👁️ Client {client_id} connected as spectator")

        client_info = ClientInfo(websocket, player_number, client_id)
        self.clients[client_id] = client_info
        
        print(f"🔌 Client {client_id} connected. Total clients: {len(self.clients)}")
        
        # אם זהו הלקוח הראשון, אתחל את המשחק
        if len(self.clients) == 1 and not self.game_initialized:
            await self.initialize_game()
        
        # שלח מצב המשחק הנוכחי ללקוח החדש (כולל מידע על השחקן שלו)
        if self.game:
            await self.send_game_state_with_player_info(websocket, player_number)

    async def unregister_client(self, websocket, client_id: str):
        """ביטול רישום לקוח"""
        if client_id in self.clients:
            client_info = self.clients[client_id]
            # שחרר את מספר השחקן
            if client_info.player_number == 1:
                self.player1_assigned = False
                print(f"🎮 Player 1 slot is now available")
            elif client_info.player_number == 2:
                self.player2_assigned = False
                print(f"🎮 Player 2 slot is now available")
            
            del self.clients[client_id]
        print(f"🔌 Client {client_id} disconnected. Total clients: {len(self.clients)}")

    async def initialize_game(self):
        """אתחול המשחק - בדיוק כמו במain.py"""
        print("🎮 Starting chess game on server...")
        print("🎮 מתחיל משחק שחמט בשרת...")

        # טען את התמונה
        print("📸 Loading board image...")
        img = Img()
        img_path = pathlib.Path(__file__).parent.parent / "board.png"
        img.read(str("C:/Users/board.png"), size=(822, 822))
        
        print("📸 Image loaded:", img.img is not None)
        if img.img is None:
            raise RuntimeError("Board image failed to load!")

        # צור את הלוח עם התמונה
        board = Board(
            cell_H_pix=103.5,
            cell_W_pix=102.75,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=img
        )
        
        pieces_root = pathlib.Path(r"C:\Users\pieces")
        factory = PieceFactory(board, pieces_root)

        start_positions = [
            # כלים שחורים בחלק העליון של הלוח (שורות 0-1)
            ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB", (3, 0)), ("KB", (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
            ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
            # כלים לבנים בחלק התחתון של הלוח (שורות 6-7)
            ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
            ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW", (3, 7)), ("KW", (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
        ]

        pieces = []
        piece_counters = {}  # Track count per piece type for unique IDs

        # צור את המשחק עם התור
        self.game = Game([], board, "Player 1", "Player 2")  # הוספת שמות שחקנים

        for p_type, cell in start_positions:
            try:
                # Create unique piece ID by adding counter
                if p_type not in piece_counters:
                    piece_counters[p_type] = 0
                unique_id = f"{p_type}{piece_counters[p_type]}"
                piece_counters[p_type] += 1
                piece = factory.create_piece(p_type, cell, self.game.user_input_queue)
                # Override the piece ID with unique ID
                piece.piece_id = unique_id
                # Update physics with the correct piece_id
                piece._state._physics.piece_id = unique_id
                pieces.append(piece)
            except Exception as e:
                print(f"בעיה עם {p_type}: {e}")

        # עדכן את המשחק עם הכלים
        self.game.pieces = pieces
        self.game_initialized = True
        
        print(f"🎮 Game initialized with {len(pieces)} pieces")
        print("🏆 ScoreSystem initialized")
        print("📝 MovesLog initialized")
        
        # התחל את הלולאה העיקרית של המשחק
        asyncio.create_task(self.game_loop())

    async def game_loop(self):
        """לולאת המשחק העיקרית"""
        if not self.game:
            return
            
        start_ms = int(time.monotonic() * 1000)
        for p in self.game.pieces:
            p.reset(start_ms)

        print("🎮 Starting game loop...")
        
        while not self.game.game_over:
            now = int(time.monotonic() * 1000)

            # (1) update physics & animations
            for p in self.game.pieces:
                p.update(now)

            # (2) update new systems - כולל מערכות הניקוד והמהלכים
            self.game.message_overlay.update(now / 1000.0)

            # (3) handle queued Commands
            while not self.game.user_input_queue.empty():
                print("📥 יש קומנד בתור!")
                cmd: Command = self.game.user_input_queue.get()
                print("📥 cmd:", cmd)
                self.game._process_input(cmd)
                
                # שלח עדכון ללקוחות אחרי עיבוד הקומנד (כולל נתוני ניקוד ומהלכים)
                await self.broadcast_game_state()
                
                if self.game.game_over:
                    break

            # (4) detect captures
            self.game._resolve_collisions()
            
            # (5) שלח עדכון מחזורי ללקוחות
            await self.broadcast_game_state()
            
            # (6) שליטה בקצב פריימים - 60 FPS
            await asyncio.sleep(1/60.0)

        print("🎮 Game loop ended")

    async def handle_client_message(self, websocket, message: str, client_id: str):
        """טיפול בהודעות מהלקוחות"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'keyboard_input':
                # טיפול בקלט מקלדת - רק אם הלקוח הוא שחקן
                key = data.get('key')
                await self.handle_keyboard_input(key, client_id)
                
            elif msg_type == 'get_game_state':
                # בקשה למצב המשחק
                client_info = self.clients.get(client_id)
                player_number = client_info.player_number if client_info else None
                await self.send_game_state_with_player_info(websocket, player_number)
                
            elif msg_type == 'ping':
                # בדיקת חיבור
                await websocket.send(json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            print(f"❌ Error handling message from client {client_id}: {e}")

    async def handle_keyboard_input(self, key: int, client_id: str):
        """טיפול בקלט מקלדת - רק השחקן המתאים יכול לשלוט"""
        if not self.game:
            return
            
        # בדוק איזה שחקן שלח את הקלט
        client_info = self.clients.get(client_id)
        if not client_info or client_info.player_number is None:
            print(f"🚫 Client {client_id} is spectator, ignoring input")
            return
            
        player_number = client_info.player_number
        print(f"\n=== KEY PRESSED by Player {player_number} ({client_id}): {key} ===")
        
        if 32 <= key <= 126:
            print(f"Character: '{chr(key)}'")
        else:
            print(f"Special key code: {key}")
        
        # Check for exit keys first (כל שחקן יכול לצאת)
        if key == 27 or key == ord('q'):  # ESC או Q
            self.game.game_over = True
            await self.broadcast_game_state()
            return
        
        # Convert to character for easier handling
        char = None
        if 32 <= key <= 126:
            char = chr(key).lower()
        
        # תמיכה מלאה במקלדת עברית
        hebrew_keys = {
            ord('\''): 'w',
            ord('ש'): 'a',
            ord('ד'): 's',
            ord('ג'): 'd'
        }
        detected_hebrew = hebrew_keys.get(key)
        if detected_hebrew:
            print(f"🔥 זוהה מקש עברי: {key} -> {detected_hebrew}")
            char = detected_hebrew
        
        # רק שחקן 2 יכול להשתמש בפקדי WASD (כלים שחורים)
        if player_number == 2:
            wasd_detected = False
            
            if (key in [119, 87] or char == 'w' or 
                key in [1493, 215, 246, 1500] or detected_hebrew == 'w'):
                print("🔥 Player 2: Moving UP (W/ו)")
                self.game._move_cursor_player2(0, -1)
                wasd_detected = True
            elif (key in [115, 83] or char == 's' or 
                  key in [1491, 212, 213, 1504] or detected_hebrew == 's'):
                print("🔥 Player 2: Moving DOWN (S/ד)")
                self.game._move_cursor_player2(0, 1)
                wasd_detected = True
            elif (key in [97, 65] or char == 'a' or 
                  key in [1513, 249, 251, 1506] or detected_hebrew == 'a'):
                print("🔥 Player 2: Moving LEFT (A/ש)")
                self.game._move_cursor_player2(-1, 0)
                wasd_detected = True
            elif (key in [100, 68] or char == 'd' or 
                  key in [1499, 235, 237, 1507] or detected_hebrew == 'd'):
                print("🔥 Player 2: Moving RIGHT (D/כ)")
                self.game._move_cursor_player2(1, 0)
                wasd_detected = True
            elif key == 32 or char == ' ':  # Space
                print("🔥 Player 2: Selecting piece (SPACE)")
                self.game._select_piece_player2()
                wasd_detected = True
            elif key == 37:  # Left Arrow
                print("🔥 Player 2: Moving LEFT (←)")
                self.game._move_cursor_player2(-1, 0)
                wasd_detected = True
            elif key == 39:  # Right Arrow
                print("🔥 Player 2: Moving RIGHT (→)")
                self.game._move_cursor_player2(1, 0)
                wasd_detected = True
            elif key == 38:  # Up Arrow
                print("🔥 Player 2: Moving UP (↑)")
                self.game._move_cursor_player2(0, -1)
                wasd_detected = True
            elif key == 40:  # Down Arrow
                print("🔥 Player 2: Moving DOWN (↓)")
                self.game._move_cursor_player2(0, 1)
                wasd_detected = True
            if not wasd_detected:
                print(f"🚫 Player 2 tried invalid key: {key}")
        
        # רק שחקן 1 יכול להשתמש בפקדי מקשי מספרים (כלים לבנים)
        elif player_number == 1:
            numpad_detected = False
            
            if key == 56 or char == '8':  # 8 key
                print("⚡ Player 1: Moving UP (8)")
                self.game._move_cursor_player1(0, -1)
                numpad_detected = True
            elif key == 50 or char == '2':  # 2 key
                print("⚡ Player 1: Moving DOWN (2)")
                self.game._move_cursor_player1(0, 1)
                numpad_detected = True
            elif key == 52 or char == '4':  # 4 key
                print("⚡ Player 1: Moving LEFT (4)")
                self.game._move_cursor_player1(-1, 0)
                numpad_detected = True
            elif key == 54 or char == '6':  # 6 key
                print("⚡ Player 1: Moving RIGHT (6)")
                self.game._move_cursor_player1(1, 0)
                numpad_detected = True
            elif key == 53 or key == 48 or char == '5' or char == '0':  # 5 or 0 key
                print("⚡ Player 1: Selecting piece (5 or 0)")
                self.game._select_piece_player1()
                numpad_detected = True
            elif key in [13, 10, 39, 226, 249]:  # Enter
                print(f"⚡ Player 1: Selecting piece (Enter code: {key})")
                self.game._select_piece_player1()
                numpad_detected = True
            
            if not numpad_detected:
                print(f"🚫 Player 1 tried invalid key: {key}")

        print("=== KEY PROCESSING COMPLETE ===\n")

    def get_game_state(self) -> GameState:
        """קבלת מצב המשחק הנוכחי כולל נתוני ניקוד ומהלכים"""
        if not self.game:
            return None
            
        pieces_data = []
        for piece in self.game.pieces:
            piece_pos = self.game._get_piece_position(piece)
            pixel_pos = getattr(piece._state._physics, 'pixel_pos', (0, 0))
            
            pieces_data.append({
                'id': piece.piece_id,
                'position': piece_pos,
                'pixel_position': pixel_pos,
                'moving': getattr(piece._state._physics, 'moving', False)
            })
        
        # איסוף נתוני ניקוד
        score_data = {
            'player1_score': self.game.score_system.player1_score,
            'player2_score': self.game.score_system.player2_score,
            'player1_name': self.game.score_system.player1_name,
            'player2_name': self.game.score_system.player2_name,
            'player1_captures': getattr(self.game.score_system, 'player1_captures', []),
            'player2_captures': getattr(self.game.score_system, 'player2_captures', [])
        }
        
        # איסוף נתוני מהלכים
        moves_data = {
            'moves_list': self.game.moves_log.moves,
            'move_count': len(self.game.moves_log.moves),
            'last_move': self.game.moves_log.moves[-1] if self.game.moves_log.moves else None
        }
        
        return GameState(
            pieces_data=pieces_data,
            board_size=(self.game.board.img.img.shape[1], self.game.board.img.img.shape[0]),
            player1_cursor=self.game.cursor_pos_player1,
            player2_cursor=self.game.cursor_pos_player2,
            selected_piece_player1=self.game.selected_piece_player1.piece_id if self.game.selected_piece_player1 else None,
            selected_piece_player2=self.game.selected_piece_player2.piece_id if self.game.selected_piece_player2 else None,
            game_over=self.game.game_over,
            winner=getattr(self.game, 'winner', None),
            score_data=score_data,
            moves_data=moves_data
        )

    async def send_game_state_with_player_info(self, websocket, player_number: Optional[int]):
        """שליחת מצב המשחק ללקוח ספציפי עם מידע על השחקן שלו"""
        game_state = self.get_game_state()
        if game_state:
            message = {
                'type': 'game_state',
                'data': {
                    'pieces': game_state.pieces_data,
                    'board_size': game_state.board_size,
                    'player1_cursor': game_state.player1_cursor,
                    'player2_cursor': game_state.player2_cursor,
                    'selected_piece_player1': game_state.selected_piece_player1,
                    'selected_piece_player2': game_state.selected_piece_player2,
                    'game_over': game_state.game_over,
                    'winner': game_state.winner,
                    'your_player': player_number,  # מידע נוסף עבור הלקוח
                    'score_data': game_state.score_data,  # הוספת נתוני ניקוד
                    'moves_data': game_state.moves_data   # הוספת נתוני מהלכים
                }
            }
            try:
                # await websocket.send(json.dumps(message))
                await websocket.send(json.dumps(message, default=lambda o: o.to_dict() if hasattr(o, 'to_dict') else str(o))
)

            except websockets.exceptions.ConnectionClosed:
                pass  # הלקוח התנתק

    async def send_game_state(self, websocket):
        """שליחת מצב המשחק ללקוח ספציפי (ללא מידע שחקן)"""
        await self.send_game_state_with_player_info(websocket, None)

    async def broadcast_game_state(self):
        """שידור מצב המשחק לכל הלקוחות"""
        if not self.clients:
            return
            
        game_state = self.get_game_state()
        if not game_state:
            return
        
        # שלח לכל הלקוחות המחוברים עם המידע המתאים להם
        disconnected_clients = []
        for client_id, client_info in self.clients.items():
            try:
                message = {
                    'type': 'game_state',
                    'data': {
                        'pieces': game_state.pieces_data,
                        'board_size': game_state.board_size,
                        'player1_cursor': game_state.player1_cursor,
                        'player2_cursor': game_state.player2_cursor,
                        'selected_piece_player1': game_state.selected_piece_player1,
                        'selected_piece_player2': game_state.selected_piece_player2,
                        'game_over': game_state.game_over,
                        'winner': game_state.winner,
                        'your_player': client_info.player_number,
                        'score_data': game_state.score_data,  # הוספת נתוני ניקוד
                        'moves_data': game_state.moves_data   # הוספת נתוני מהלכים
                    }
                }
                
                # await client_info.websocket.send(json.dumps(message))
                await client_info.websocket.send(json.dumps(message, default=lambda o: o.to_dict() if hasattr(o, 'to_dict') else str(o))
)

            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
        
        # הסר לקוחות מנותקים
        for client_id in disconnected_clients:
            await self.unregister_client(None, client_id)

    async def handle_client(self, websocket):
        """טיפול בלקוח חדש"""
        client_id = f"client_{int(time.time() * 1000)}"  # ID ייחודי יותר
        await self.register_client(websocket, client_id)
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message, client_id)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket, client_id)

async def main():
    server = ChessServer()
    
    print("🚀 Starting Chess Server with Score & Moves Tracking...")
    print("🎮 First client will be Player 1 (White pieces)")
    print("🎮 Second client will be Player 2 (Black pieces)")
    print("👁️ Additional clients will be spectators")
    print("🏆 Score and moves tracking enabled")
    
    async with websockets.serve(server.handle_client, "localhost", 8765):
        print("Chess server started on ws://localhost:8765")
        await asyncio.Future()  # רץ לנצח

if __name__ == "__main__":
    asyncio.run(main())
# import asyncio
# import websockets
# import json
# import pathlib
# import time
# from typing import Dict, List, Optional
# from dataclasses import dataclass

# # Import your existing classes
# from It1_interfaces.img import Img
# from It1_interfaces.Board import Board
# from It1_interfaces.Game import Game
# from It1_interfaces.PieceFactory import PieceFactory
# from It1_interfaces.Command import Command
# import queue

# @dataclass
# class GameState:
#     """מחלקה לשמירת מצב המשחק"""
#     pieces_data: List[Dict]
#     board_size: tuple
#     player1_cursor: List[int]
#     player2_cursor: List[int]
#     selected_piece_player1: Optional[str]
#     selected_piece_player2: Optional[str]
#     game_over: bool
#     winner: Optional[str]
#     # הוספת נתוני ניקוד ומהלכים
#     score_data: Dict
#     moves_data: Dict

# @dataclass
# class ClientInfo:
#     """מידע על לקוח"""
#     websocket: websockets.WebSocketServerProtocol
#     player_number: Optional[int]  # 1 או 2, None אם צופה
#     client_id: str

# class ChessServer:
#     def __init__(self):
#         self.clients: Dict[str, ClientInfo] = {}  # client_id -> ClientInfo
#         self.game: Optional[Game] = None
#         self.game_initialized = False
#         self.player1_assigned = False
#         self.player2_assigned = False
        
#     async def register_client(self, websocket, client_id: str):
#         """רישום לקוח חדש"""
#         # קבע איזה שחקן הוא (1, 2, או צופה)
#         player_number = None
#         if not self.player1_assigned:
#             player_number = 1
#             self.player1_assigned = True
#             print(f"🎮 Client {client_id} assigned as Player 1 (White pieces)")
#         elif not self.player2_assigned:
#             player_number = 2
#             self.player2_assigned = True
#             print(f"🎮 Client {client_id} assigned as Player 2 (Black pieces)")
#         else:
#             print(f"👁️ Client {client_id} connected as spectator")

#         client_info = ClientInfo(websocket, player_number, client_id)
#         self.clients[client_id] = client_info
        
#         print(f"🔌 Client {client_id} connected. Total clients: {len(self.clients)}")
        
#         # אם זהו הלקוח הראשון, אתחל את המשחק
#         if len(self.clients) == 1 and not self.game_initialized:
#             await self.initialize_game()
        
#         # שלח מצב המשחק הנוכחי ללקוח החדש (כולל מידע על השחקן שלו)
#         if self.game:
#             await self.send_game_state_with_player_info(websocket, player_number)

#     async def unregister_client(self, websocket, client_id: str):
#         """ביטול רישום לקוח"""
#         if client_id in self.clients:
#             client_info = self.clients[client_id]
#             # שחרר את מספר השחקן
#             if client_info.player_number == 1:
#                 self.player1_assigned = False
#                 print(f"🎮 Player 1 slot is now available")
#             elif client_info.player_number == 2:
#                 self.player2_assigned = False
#                 print(f"🎮 Player 2 slot is now available")
            
#             del self.clients[client_id]
#         print(f"🔌 Client {client_id} disconnected. Total clients: {len(self.clients)}")

#     async def initialize_game(self):
#         """אתחול המשחק - בדיוק כמו במain.py"""
#         print("🎮 Starting chess game on server...")
#         print("🎮 מתחיל משחק שחמט בשרת...")

#         # טען את התמונה
#         print("📸 Loading board image...")
#         img = Img()
#         img_path = pathlib.Path(__file__).parent.parent / "board.png"
#         img.read(str("C:/Users/board.png"), size=(822, 822))
        
#         print("📸 Image loaded:", img.img is not None)
#         if img.img is None:
#             raise RuntimeError("Board image failed to load!")

#         # צור את הלוח עם התמונה
#         board = Board(
#             cell_H_pix=103.5,
#             cell_W_pix=102.75,
#             cell_H_m=1,
#             cell_W_m=1,
#             W_cells=8,
#             H_cells=8,
#             img=img
#         )
        
#         pieces_root = pathlib.Path(r"C:\Users\pieces")
#         factory = PieceFactory(board, pieces_root)

#         start_positions = [
#             # כלים שחורים בחלק העליון של הלוח (שורות 0-1)
#             ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB", (3, 0)), ("KB", (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
#             ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
#             # כלים לבנים בחלק התחתון של הלוח (שורות 6-7)
#             ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
#             ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW", (3, 7)), ("KW", (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
#         ]

#         pieces = []
#         piece_counters = {}  # Track count per piece type for unique IDs

#         # צור את המשחק עם התור
#         self.game = Game([], board, "Player 1", "Player 2")  # הוספת שמות שחקנים

#         for p_type, cell in start_positions:
#             try:
#                 # Create unique piece ID by adding counter
#                 if p_type not in piece_counters:
#                     piece_counters[p_type] = 0
#                 unique_id = f"{p_type}{piece_counters[p_type]}"
#                 piece_counters[p_type] += 1
#                 piece = factory.create_piece(p_type, cell, self.game.user_input_queue)
#                 # Override the piece ID with unique ID
#                 piece.piece_id = unique_id
#                 # Update physics with the correct piece_id
#                 piece._state._physics.piece_id = unique_id
#                 pieces.append(piece)
#             except Exception as e:
#                 print(f"בעיה עם {p_type}: {e}")

#         # עדכן את המשחק עם הכלים
#         self.game.pieces = pieces
        
#         # וודא שיש מערכת מהלכים
#         if not hasattr(self.game, 'moves_log'):
#             class SimpleMoves:
#                 def __init__(self):
#                     self.moves = []
#             self.game.moves_log = SimpleMoves()
        
#         self.game_initialized = True
        
#         print(f"🎮 Game initialized with {len(pieces)} pieces")
#         print("🏆 ScoreSystem initialized")
#         print("📝 MovesLog initialized")
        
#         # התחל את הלולאה העיקרית של המשחק
#         asyncio.create_task(self.game_loop())

#     def record_move_manually(self, piece_id: str, from_pos: tuple, to_pos: tuple):
#         """רישום מהלך ידני במקום להסתמך על EventSystem"""
#         if not self.game:
#             return
            
#         # יצירת entry של מהלך
#         move_entry = {
#             'piece_id': piece_id,
#             'from_position': from_pos,
#             'to_position': to_pos,
#             'description': f"{from_pos} -> {to_pos}",
#             'timestamp': int(time.time() * 1000)
#         }
        
#         # וודא שיש מערכת מהלכים
#         if not hasattr(self.game, 'moves_log'):
#             # צור אובייקט פשוט עם רשימת מהלכים
#             class SimpleMoves:
#                 def __init__(self):
#                     self.moves = []
#             self.game.moves_log = SimpleMoves()
        
#         # וודא שיש רשימת מהלכים
#         if not hasattr(self.game.moves_log, 'moves'):
#             self.game.moves_log.moves = []
        
#         self.game.moves_log.moves.append(move_entry)
        
#         print(f"📝 Manually recorded move: {piece_id} from {from_pos} to {to_pos}")
#         print(f"📝 Total moves recorded: {len(self.game.moves_log.moves)}")

#     async def game_loop(self):
#         """לולאת המשחק העיקרית"""
#         if not self.game:
#             return
            
#         start_ms = int(time.monotonic() * 1000)
#         for p in self.game.pieces:
#             p.reset(start_ms)

#         print("🎮 Starting game loop...")
        
#         # שמור מיקומי כלים קודמים לזיהוי מהלכים
#         previous_positions = {}
#         for piece in self.game.pieces:
#             previous_positions[piece.piece_id] = self.game._get_piece_position(piece)
        
#         while not self.game.game_over:
#             now = int(time.monotonic() * 1000)

#             # (1) update physics & animations
#             for p in self.game.pieces:
#                 p.update(now)

#             # (2) update new systems - כולל מערכות הניקוד והמהלכים
#             self.game.message_overlay.update(now / 1000.0)

#             # (3) handle queued Commands
#             while not self.game.user_input_queue.empty():
#                 print("📥 יש קומנד בתור!")
#                 cmd: Command = self.game.user_input_queue.get()
#                 print("📥 cmd:", cmd)
                
#                 # שמור מיקומים לפני עיבוד הקומנד
#                 before_positions = {}
#                 for piece in self.game.pieces:
#                     before_positions[piece.piece_id] = self.game._get_piece_position(piece)
                
#                 self.game._process_input(cmd)
                
#                 # בדוק אילו כלים זזו ורשום מהלכים
#                 for piece in self.game.pieces:
#                     current_pos = self.game._get_piece_position(piece)
#                     previous_pos = before_positions.get(piece.piece_id)
                    
#                     if previous_pos and current_pos != previous_pos:
#                         # הכלי זז - רשום מהלך
#                         self.record_move_manually(piece.piece_id, previous_pos, current_pos)
                
#                 # שלח עדכון ללקוחות אחרי עיבוד הקומנד (כולל נתוני ניקוד ומהלכים)
#                 await self.broadcast_game_state()
                
#                 if self.game.game_over:
#                     break

#             # (4) detect captures
#             self.game._resolve_collisions()
            
#             # (5) שלח עדכון מחזורי ללקוחות
#             await self.broadcast_game_state()
            
#             # (6) שליטה בקצב פריימים - 60 FPS
#             await asyncio.sleep(1/60.0)

#         print("🎮 Game loop ended")

#     async def handle_client_message(self, websocket, message: str, client_id: str):
#         """טיפול בהודעות מהלקוחות"""
#         try:
#             data = json.loads(message)
#             msg_type = data.get('type')
            
#             if msg_type == 'keyboard_input':
#                 # טיפול בקלט מקלדת - רק אם הלקוח הוא שחקן
#                 key = data.get('key')
#                 await self.handle_keyboard_input(key, client_id)
                
#             elif msg_type == 'get_game_state':
#                 # בקשה למצב המשחק
#                 client_info = self.clients.get(client_id)
#                 player_number = client_info.player_number if client_info else None
#                 await self.send_game_state_with_player_info(websocket, player_number)
                
#             elif msg_type == 'ping':
#                 # בדיקת חיבור
#                 await websocket.send(json.dumps({'type': 'pong'}))
                
#         except json.JSONDecodeError:
#             print(f"❌ Invalid JSON from client {client_id}: {message}")
#         except Exception as e:
#             print(f"❌ Error handling message from client {client_id}: {e}")

#     async def handle_keyboard_input(self, key: int, client_id: str):
#         """טיפול בקלט מקלדת - רק השחקן המתאים יכול לשלוט"""
#         if not self.game:
#             return
            
#         # בדוק איזה שחקן שלח את הקלט
#         client_info = self.clients.get(client_id)
#         if not client_info or client_info.player_number is None:
#             print(f"🚫 Client {client_id} is spectator, ignoring input")
#             return
            
#         player_number = client_info.player_number
#         print(f"\n=== KEY PRESSED by Player {player_number} ({client_id}): {key} ===")
        
#         if 32 <= key <= 126:
#             print(f"Character: '{chr(key)}'")
#         else:
#             print(f"Special key code: {key}")
        
#         # Check for exit keys first (כל שחקן יכול לצאת)
#         if key == 27 or key == ord('q'):  # ESC או Q
#             self.game.game_over = True
#             await self.broadcast_game_state()
#             return
        
#         # Convert to character for easier handling
#         char = None
#         if 32 <= key <= 126:
#             char = chr(key).lower()
        
#         # תמיכה מלאה במקלדת עברית
#         hebrew_keys = {
#             ord('\''): 'w',
#             ord('ש'): 'a',
#             ord('ד'): 's',
#             ord('ג'): 'd'
#         }
#         detected_hebrew = hebrew_keys.get(key)
#         if detected_hebrew:
#             print(f"🔥 זוהה מקש עברי: {key} -> {detected_hebrew}")
#             char = detected_hebrew
        
#         # רק שחקן 2 יכול להשתמש בפקדי WASD (כלים שחורים)
#         if player_number == 2:
#             wasd_detected = False
            
#             if (key in [119, 87] or char == 'w' or 
#                 key in [1493, 215, 246, 1500] or detected_hebrew == 'w'):
#                 print("🔥 Player 2: Moving UP (W/ו)")
#                 self.game._move_cursor_player2(0, -1)
#                 wasd_detected = True
#             elif (key in [115, 83] or char == 's' or 
#                   key in [1491, 212, 213, 1504] or detected_hebrew == 's'):
#                 print("🔥 Player 2: Moving DOWN (S/ד)")
#                 self.game._move_cursor_player2(0, 1)
#                 wasd_detected = True
#             elif (key in [97, 65] or char == 'a' or 
#                   key in [1513, 249, 251, 1506] or detected_hebrew == 'a'):
#                 print("🔥 Player 2: Moving LEFT (A/ש)")
#                 self.game._move_cursor_player2(-1, 0)
#                 wasd_detected = True
#             elif (key in [100, 68] or char == 'd' or 
#                   key in [1499, 235, 237, 1507] or detected_hebrew == 'd'):
#                 print("🔥 Player 2: Moving RIGHT (D/כ)")
#                 self.game._move_cursor_player2(1, 0)
#                 wasd_detected = True
#             elif key == 32 or char == ' ':  # Space
#                 print("🔥 Player 2: Selecting piece (SPACE)")
#                 self.game._select_piece_player2()
#                 wasd_detected = True
#             elif key == 37:  # Left Arrow
#                 print("🔥 Player 2: Moving LEFT (←)")
#                 self.game._move_cursor_player2(-1, 0)
#                 wasd_detected = True
#             elif key == 39:  # Right Arrow
#                 print("🔥 Player 2: Moving RIGHT (→)")
#                 self.game._move_cursor_player2(1, 0)
#                 wasd_detected = True
#             elif key == 38:  # Up Arrow
#                 print("🔥 Player 2: Moving UP (↑)")
#                 self.game._move_cursor_player2(0, -1)
#                 wasd_detected = True
#             elif key == 40:  # Down Arrow
#                 print("🔥 Player 2: Moving DOWN (↓)")
#                 self.game._move_cursor_player2(0, 1)
#                 wasd_detected = True
#             if not wasd_detected:
#                 print(f"🚫 Player 2 tried invalid key: {key}")
        
#         # רק שחקן 1 יכול להשתמש בפקדי מקשי מספרים (כלים לבנים)
#         elif player_number == 1:
#             numpad_detected = False
            
#             if key == 56 or char == '8':  # 8 key
#                 print("⚡ Player 1: Moving UP (8)")
#                 self.game._move_cursor_player1(0, -1)
#                 numpad_detected = True
#             elif key == 50 or char == '2':  # 2 key
#                 print("⚡ Player 1: Moving DOWN (2)")
#                 self.game._move_cursor_player1(0, 1)
#                 numpad_detected = True
#             elif key == 52 or char == '4':  # 4 key
#                 print("⚡ Player 1: Moving LEFT (4)")
#                 self.game._move_cursor_player1(-1, 0)
#                 numpad_detected = True
#             elif key == 54 or char == '6':  # 6 key
#                 print("⚡ Player 1: Moving RIGHT (6)")
#                 self.game._move_cursor_player1(1, 0)
#                 numpad_detected = True
#             elif key == 53 or key == 48 or char == '5' or char == '0':  # 5 or 0 key
#                 print("⚡ Player 1: Selecting piece (5 or 0)")
#                 self.game._select_piece_player1()
#                 numpad_detected = True
#             elif key in [13, 10, 39, 226, 249]:  # Enter
#                 print(f"⚡ Player 1: Selecting piece (Enter code: {key})")
#                 self.game._select_piece_player1()
#                 numpad_detected = True
            
#             if not numpad_detected:
#                 print(f"🚫 Player 1 tried invalid key: {key}")

#         print("=== KEY PROCESSING COMPLETE ===\n")

#     def get_game_state(self) -> GameState:
#         """קבלת מצב המשחק הנוכחי כולל נתוני ניקוד ומהלכים"""
#         if not self.game:
#             return None
            
#         pieces_data = []
#         for piece in self.game.pieces:
#             piece_pos = self.game._get_piece_position(piece)
#             pixel_pos = getattr(piece._state._physics, 'pixel_pos', (0, 0))
            
#             pieces_data.append({
#                 'id': piece.piece_id,
#                 'position': piece_pos,
#                 'pixel_position': pixel_pos,
#                 'moving': getattr(piece._state._physics, 'moving', False)
#             })
        
#         # איסוף נתוני ניקוד
#         score_data = {
#             'player1_score': self.game.score_system.player1_score,
#             'player2_score': self.game.score_system.player2_score,
#             'player1_name': self.game.score_system.player1_name,
#             'player2_name': self.game.score_system.player2_name,
#             'player1_captures': getattr(self.game.score_system, 'player1_captures', []),
#             'player2_captures': getattr(self.game.score_system, 'player2_captures', [])
#         }
        
#         # איסוף נתוני מהלכים - תיקון כאן!
#         moves_list = []
#         if hasattr(self.game, 'moves_log') and hasattr(self.game.moves_log, 'moves'):
#             moves_list = self.game.moves_log.moves
        
#         moves_data = {
#             'moves_list': moves_list,
#             'move_count': len(moves_list),
#             'last_move': moves_list[-1] if moves_list else None
#         }
        
#         return GameState(
#             pieces_data=pieces_data,
#             board_size=(self.game.board.img.img.shape[1], self.game.board.img.img.shape[0]),
#             player1_cursor=self.game.cursor_pos_player1,
#             player2_cursor=self.game.cursor_pos_player2,
#             selected_piece_player1=self.game.selected_piece_player1.piece_id if self.game.selected_piece_player1 else None,
#             selected_piece_player2=self.game.selected_piece_player2.piece_id if self.game.selected_piece_player2 else None,
#             game_over=self.game.game_over,
#             winner=getattr(self.game, 'winner', None),
#             score_data=score_data,
#             moves_data=moves_data
#         )

#     async def send_game_state_with_player_info(self, websocket, player_number: Optional[int]):
#         """שליחת מצב המשחק ללקוח ספציפי עם מידע על השחקן שלו"""
#         game_state = self.get_game_state()
#         if game_state:
#             message = {
#                 'type': 'game_state',
#                 'data': {
#                     'pieces': game_state.pieces_data,
#                     'board_size': game_state.board_size,
#                     'player1_cursor': game_state.player1_cursor,
#                     'player2_cursor': game_state.player2_cursor,
#                     'selected_piece_player1': game_state.selected_piece_player1,
#                     'selected_piece_player2': game_state.selected_piece_player2,
#                     'game_over': game_state.game_over,
#                     'winner': game_state.winner,
#                     'your_player': player_number,  # מידע נוסף עבור הלקוח
#                     'score_data': game_state.score_data,  # הוספת נתוני ניקוד
#                     'moves_data': game_state.moves_data   # הוספת נתוני מהלכים
#                 }
#             }
#             try:
#                 # מרוקן json serialization פשוט יותר
#                 json_str = json.dumps(message, default=str, ensure_ascii=False)
#                 await websocket.send(json_str)
#             except websockets.exceptions.ConnectionClosed:
#                 pass  # הלקוח התנתק

#     async def send_game_state(self, websocket):
#         """שליחת מצב המשחק ללקוח ספציפי (ללא מידע שחקן)"""
#         await self.send_game_state_with_player_info(websocket, None)

#     async def broadcast_game_state(self):
#         """שידור מצב המשחק לכל הלקוחות"""
#         if not self.clients:
#             return
            
#         game_state = self.get_game_state()
#         if not game_state:
#             return
        
#         # שלח לכל הלקוחות המחוברים עם המידע המתאים להם
#         disconnected_clients = []
#         for client_id, client_info in self.clients.items():
#             try:
#                 message = {
#                     'type': 'game_state',
#                     'data': {
#                         'pieces': game_state.pieces_data,
#                         'board_size': game_state.board_size,
#                         'player1_cursor': game_state.player1_cursor,
#                         'player2_cursor': game_state.player2_cursor,
#                         'selected_piece_player1': game_state.selected_piece_player1,
#                         'selected_piece_player2': game_state.selected_piece_player2,
#                         'game_over': game_state.game_over,
#                         'winner': game_state.winner,
#                         'your_player': client_info.player_number,
#                         'score_data': game_state.score_data,  # הוספת נתוני ניקוד
#                         'moves_data': game_state.moves_data   # הוספת נתוני מהלכים
#                     }
#                 }
                
#                 # מרוקן json serialization פשוט יותר
#                 json_str = json.dumps(message, default=str, ensure_ascii=False)
#                 await client_info.websocket.send(json_str)

#             except websockets.exceptions.ConnectionClosed:
#                 disconnected_clients.append(client_id)
        
#         # הסר לקוחות מנותקים
#         for client_id in disconnected_clients:
#             await self.unregister_client(None, client_id)

#     async def handle_client(self, websocket):
#         """טיפול בלקוח חדש"""
#         client_id = f"client_{int(time.time() * 1000)}"  # ID ייחודי יותר
#         await self.register_client(websocket, client_id)
        
#         try:
#             async for message in websocket:
#                 await self.handle_client_message(websocket, message, client_id)
#         except websockets.exceptions.ConnectionClosed:
#             pass
#         finally:
#             await self.unregister_client(websocket, client_id)

# async def main():
#     server = ChessServer()
    
#     print("🚀 Starting Chess Server with Score & Moves Tracking...")
#     print("🎮 First client will be Player 1 (White pieces)")
#     print("🎮 Second client will be Player 2 (Black pieces)")
#     print("👁️ Additional clients will be spectators")
#     print("🏆 Score and moves tracking enabled")
#     print("📝 Fixed moves logging system")
    
#     async with websockets.serve(server.handle_client, "localhost", 8765):
#         print("Chess server started on ws://localhost:8765")
#         await asyncio.Future()  # רץ לנצח

# if __name__ == "__main__":
#     asyncio.run(main())