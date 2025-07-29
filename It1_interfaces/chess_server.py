import asyncio
import websockets
import json
import pathlib
from typing import Dict, List, Tuple, Optional
import time
import logging

# Import your existing classes
import sys
sys.path.append(str(pathlib.Path(__file__).parent))

from It1_interfaces.Board import Board
from It1_interfaces.img import Img
from It1_interfaces.PieceFactory import PieceFactory
from It1_interfaces.Piece import Piece

class ChessGameServer:
    def __init__(self):
        """Initialize the chess game server."""
        self.games: Dict[str, GameSession] = {}
        self.waiting_players: List[websockets.WebSocketServerProtocol] = []
        self.player_to_game: Dict[websockets.WebSocketServerProtocol, str] = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize board and pieces
        self._setup_game_template()
    
    def _setup_game_template(self):
        """Setup the initial board and piece configuration."""
        # Load board image
        img = Img()
        img_path = pathlib.Path(__file__).parent.parent / "board.png"
        # img.read(str(img_path), size=(822, 822))
        img.read(str("C:/Users/board.png"), size=(822, 822))

        if img.img is None:
            raise RuntimeError("Board image failed to load!")
        
        # Create board
        self.board_template = Board(
            cell_H_pix=103.5,
            cell_W_pix=102.75,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=img
        )
        
        # Setup piece factory
        pieces_root = pathlib.Path(r"C:\Users\סולי\Downloads\chess\chess\CTD25\pieces")
        self.piece_factory = PieceFactory(self.board_template, pieces_root)
        
        # Initial positions
        self.start_positions = [
            # Black pieces (top of board, rows 0-1)
            ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB", (3, 0)), 
            ("KB", (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
            ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), 
            ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
            # White pieces (bottom of board, rows 6-7)
            ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), 
            ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
            ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW", (3, 7)), 
            ("KW", (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
        ]

    async def handle_client(self, websocket, path):
        """Handle new client connection."""
        try:
            self.logger.info(f"New client connected: {websocket.remote_address}")
            
            # Add to waiting players
            self.waiting_players.append(websocket)
            
            # Try to match players
            await self._try_match_players()
            
            # Handle messages from this client
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            await self._cleanup_client(websocket)

    async def _try_match_players(self):
        """Match two waiting players into a game."""
        if len(self.waiting_players) >= 2:
            player1 = self.waiting_players.pop(0)
            player2 = self.waiting_players.pop(0)
            
            # Create new game session
            game_id = f"game_{int(time.time())}"
            game_session = GameSession(game_id, player1, player2, self.board_template, 
                                     self.piece_factory, self.start_positions)
            
            self.games[game_id] = game_session
            self.player_to_game[player1] = game_id
            self.player_to_game[player2] = game_id
            
            # Notify players that game started
            await self._send_to_player(player1, {
                "type": "game_started",
                "game_id": game_id,
                "player_color": "white",
                "opponent": str(player2.remote_address)
            })
            
            await self._send_to_player(player2, {
                "type": "game_started", 
                "game_id": game_id,
                "player_color": "black",
                "opponent": str(player1.remote_address)
            })
            
            # Send initial board state
            await game_session.send_board_state()
            
            self.logger.info(f"Game {game_id} started between {player1.remote_address} and {player2.remote_address}")

    async def _handle_message(self, websocket, message):
        """Handle message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "move":
                await self._handle_move(websocket, data)
            elif message_type == "select_piece":
                await self._handle_piece_selection(websocket, data)
            elif message_type == "ping":
                await self._send_to_player(websocket, {"type": "pong"})
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_move(self, websocket, data):
        """Handle move request from client."""
        game_id = self.player_to_game.get(websocket)
        if not game_id or game_id not in self.games:
            await self._send_error(websocket, "Not in a game")
            return
            
        game_session = self.games[game_id]
        await game_session.handle_move(websocket, data)

    async def _handle_piece_selection(self, websocket, data):
        """Handle piece selection from client."""
        game_id = self.player_to_game.get(websocket)
        if not game_id or game_id not in self.games:
            await self._send_error(websocket, "Not in a game")
            return
            
        game_session = self.games[game_id]
        await game_session.handle_piece_selection(websocket, data)

    async def _send_to_player(self, websocket, data):
        """Send data to specific player."""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _send_error(self, websocket, error_message):
        """Send error message to client."""
        await self._send_to_player(websocket, {
            "type": "error",
            "message": error_message
        })

    async def _cleanup_client(self, websocket):
        """Clean up when client disconnects."""
        # Remove from waiting players
        if websocket in self.waiting_players:
            self.waiting_players.remove(websocket)
        
        # Handle game cleanup
        game_id = self.player_to_game.get(websocket)
        if game_id and game_id in self.games:
            game_session = self.games[game_id]
            await game_session.handle_player_disconnect(websocket)
            
            # If game is empty, remove it
            if game_session.is_empty():
                del self.games[game_id]
        
        # Remove from player mapping
        if websocket in self.player_to_game:
            del self.player_to_game[websocket]


class GameSession:
    def __init__(self, game_id: str, player1, player2, board_template, piece_factory, start_positions):
        """Initialize a game session between two players."""
        self.game_id = game_id
        self.player1 = player1  # White pieces
        self.player2 = player2  # Black pieces
        self.board = board_template.clone()
        self.piece_factory = piece_factory
        
        # Game state
        self.pieces: List[Piece] = []
        self.game_over = False
        self.winner = None
        self.current_turn = "white"  # White starts first in chess
        
        # Selected pieces per player
        self.selected_piece_player1 = None
        self.selected_piece_player2 = None
        
        # Initialize pieces
        self._initialize_pieces(start_positions)
        
        # Setup logging
        self.logger = logging.getLogger(f"GameSession-{game_id}")

    def _initialize_pieces(self, start_positions):
        """Initialize all pieces on the board."""
        piece_counters = {}
        
        for p_type, cell in start_positions:
            try:
                # Create unique piece ID
                if p_type not in piece_counters:
                    piece_counters[p_type] = 0
                unique_id = f"{p_type}{piece_counters[p_type]}"
                piece_counters[p_type] += 1
                
                # Create piece (without game queue for server)
                piece = self.piece_factory.create_piece(p_type, cell, None)
                piece.piece_id = unique_id
                piece._state._physics.piece_id = unique_id
                self.pieces.append(piece)
                
            except Exception as e:
                self.logger.error(f"Error creating piece {p_type}: {e}")

    async def handle_move(self, websocket, data):
        """Handle move request."""
        try:
            piece_id = data.get("piece_id")
            target = tuple(data.get("target", []))
            
            # Validate player turn
            player_color = "white" if websocket == self.player1 else "black"
            if player_color != self.current_turn:
                await self._send_to_player(websocket, {
                    "type": "error",
                    "message": "Not your turn"
                })
                return
            
            # Find the piece
            piece = self._find_piece(piece_id)
            if not piece:
                await self._send_error(websocket, "Piece not found")
                return
            
            # Validate piece ownership
            if not self._is_player_piece(piece, player_color):
                await self._send_error(websocket, "Not your piece")
                return
            
            # Validate move
            if not self._is_valid_move(piece, target):
                await self._send_error(websocket, "Invalid move")
                return
            
            # Execute move
            await self._execute_move(piece, target)
            
            # Switch turns
            self.current_turn = "black" if self.current_turn == "white" else "white"
            
            # Send updated board state
            await self.send_board_state()
            
            # Check for game over
            if self._check_game_over():
                await self._handle_game_over()
                
        except Exception as e:
            self.logger.error(f"Error handling move: {e}")
            await self._send_error(websocket, "Move failed")

    async def handle_piece_selection(self, websocket, data):
        """Handle piece selection."""
        try:
            piece_id = data.get("piece_id")
            position = tuple(data.get("position", []))
            
            player_color = "white" if websocket == self.player1 else "black"
            
            if player_color == "white":
                if self.selected_piece_player1:
                    # Move selected piece
                    await self.handle_move(websocket, {
                        "piece_id": self.selected_piece_player1.piece_id,
                        "target": position
                    })
                    self.selected_piece_player1 = None
                else:
                    # Select piece
                    piece = self._find_piece_at_position(position)
                    if piece and self._is_player_piece(piece, "white"):
                        self.selected_piece_player1 = piece
            else:
                if self.selected_piece_player2:
                    # Move selected piece
                    await self.handle_move(websocket, {
                        "piece_id": self.selected_piece_player2.piece_id,
                        "target": position
                    })
                    self.selected_piece_player2 = None
                else:
                    # Select piece
                    piece = self._find_piece_at_position(position)
                    if piece and self._is_player_piece(piece, "black"):
                        self.selected_piece_player2 = piece
            
            # Send selection update
            await self._send_selection_update()
            
        except Exception as e:
            self.logger.error(f"Error handling piece selection: {e}")

    async def _execute_move(self, piece, target):
        """Execute a move on the server side."""
        old_position = self._get_piece_position(piece)
        
        # Check for capture
        target_piece = self._find_piece_at_position(target)
        if target_piece and target_piece != piece:
            # Remove captured piece
            self.pieces.remove(target_piece)
            self.logger.info(f"Piece {target_piece.piece_id} captured by {piece.piece_id}")
        
        # Update piece position
        piece._state._physics.cell = target
        piece._state._physics.pixel_pos = self.board.cell_to_pixel(target)
        
        # Check for pawn promotion
        self._check_pawn_promotion(piece, target)
        
        self.logger.info(f"Move executed: {piece.piece_id} from {old_position} to {target}")

    def _check_pawn_promotion(self, piece, target_pos):
        """Check and handle pawn promotion."""
        if not piece.piece_id.startswith('P'):
            return
            
        col, row = target_pos
        is_white_pawn = 'W' in piece.piece_id
        is_black_pawn = 'B' in piece.piece_id
        
        should_promote = False
        new_piece_type = None
        
        if is_white_pawn and row == 0:
            should_promote = True
            new_piece_type = "QW"
        elif is_black_pawn and row == 7:
            should_promote = True
            new_piece_type = "QB"
            
        if should_promote:
            # Create new queen
            existing_queens = [p for p in self.pieces if p.piece_id.startswith(new_piece_type)]
            queen_id = f"{new_piece_type}{len(existing_queens)}"
            
            # Remove pawn and add queen
            self.pieces.remove(piece)
            new_queen = self.piece_factory.create_piece(new_piece_type, target_pos, None)
            new_queen.piece_id = queen_id
            new_queen._state._physics.piece_id = queen_id
            self.pieces.append(new_queen)
            
            self.logger.info(f"Pawn promotion: {piece.piece_id} -> {queen_id}")

    def _is_valid_move(self, piece, target):
        """Validate if move is legal."""
        # Basic boundary check
        if not (0 <= target[0] <= 7 and 0 <= target[1] <= 7):
            return False
        
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            return False
        
        # Check piece movement rules using existing logic
        if hasattr(piece._state, '_moves') and hasattr(piece._state._moves, 'valid_moves'):
            dx = target[0] - current_pos[0]
            dy = target[1] - current_pos[1]
            
            valid_moves = piece._state._moves.valid_moves
            move_is_valid = False
            
            for move_dx, move_dy, move_type in valid_moves:
                if dx == move_dx and dy == move_dy:
                    move_is_valid = True
                    break
            
            if not move_is_valid:
                return False
            
            # Check path is clear (except for knights)
            if not piece.piece_id.startswith('N'):
                if self._is_path_blocked(current_pos, target):
                    return False
        
        # Check target square
        target_piece = self._find_piece_at_position(target)
        if target_piece:
            # Can't capture own piece
            piece_color = "white" if 'W' in piece.piece_id else "black"
            target_color = "white" if 'W' in target_piece.piece_id else "black"
            if piece_color == target_color:
                return False
        
        return True

    def _is_path_blocked(self, start, end):
        """Check if path between start and end is blocked."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        if dx == 0 and dy == 0:
            return False
        
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        current_x = start[0] + step_x
        current_y = start[1] + step_y
        
        while (current_x, current_y) != end:
            if self._find_piece_at_position((current_x, current_y)):
                return True
            current_x += step_x
            current_y += step_y
        
        return False

    def _find_piece(self, piece_id):
        """Find piece by ID."""
        for piece in self.pieces:
            if piece.piece_id == piece_id:
                return piece
        return None

    def _find_piece_at_position(self, position):
        """Find piece at given position."""
        for piece in self.pieces:
            piece_pos = self._get_piece_position(piece)
            if piece_pos == position:
                return piece
        return None

    def _get_piece_position(self, piece):
        """Get piece position."""
        if hasattr(piece._state, '_physics') and hasattr(piece._state._physics, 'cell'):
            return piece._state._physics.cell
        return None

    def _is_player_piece(self, piece, color):
        """Check if piece belongs to player."""
        if color == "white":
            return 'W' in piece.piece_id
        else:
            return 'B' in piece.piece_id

    def _check_game_over(self):
        """Check if game is over."""
        white_king = None
        black_king = None
        
        for piece in self.pieces:
            if piece.piece_id == "KW0":
                white_king = piece
            elif piece.piece_id == "KB0":
                black_king = piece
        
        if not white_king:
            self.winner = "black"
            self.game_over = True
            return True
        elif not black_king:
            self.winner = "white"
            self.game_over = True
            return True
        
        return False

    async def _handle_game_over(self):
        """Handle game over."""
        message = {
            "type": "game_over",
            "winner": self.winner
        }
        
        if self.player1:
            await self._send_to_player(self.player1, message)
        if self.player2:
            await self._send_to_player(self.player2, message)

    async def send_board_state(self):
        """Send current board state to both players."""
        pieces_data = []
        for piece in self.pieces:
            pos = self._get_piece_position(piece)
            if pos:
                pieces_data.append({
                    "id": piece.piece_id,
                    "position": pos,
                    "type": piece.piece_id[:-1]  # Remove number suffix
                })
        
        board_state = {
            "type": "board_state",
            "pieces": pieces_data,
            "current_turn": self.current_turn,
            "game_over": self.game_over,
            "winner": self.winner
        }
        
        if self.player1:
            await self._send_to_player(self.player1, board_state)
        if self.player2:
            await self._send_to_player(self.player2, board_state)

    async def _send_selection_update(self):
        """Send piece selection updates."""
        selection_data = {
            "type": "selection_update",
            "selected_white": self.selected_piece_player1.piece_id if self.selected_piece_player1 else None,
            "selected_black": self.selected_piece_player2.piece_id if self.selected_piece_player2 else None
        }
        
        if self.player1:
            await self._send_to_player(self.player1, selection_data)
        if self.player2:
            await self._send_to_player(self.player2, selection_data)

    async def handle_player_disconnect(self, websocket):
        """Handle player disconnection."""
        if websocket == self.player1:
            self.player1 = None
            if self.player2:
                await self._send_to_player(self.player2, {
                    "type": "player_disconnected",
                    "message": "Opponent disconnected"
                })
        elif websocket == self.player2:
            self.player2 = None
            if self.player1:
                await self._send_to_player(self.player1, {
                    "type": "player_disconnected", 
                    "message": "Opponent disconnected"
                })

    def is_empty(self):
        """Check if game session is empty."""
        return self.player1 is None and self.player2 is None

    async def _send_to_player(self, websocket, data):
        """Send data to specific player."""
        try:
            await websocket.send(json.dumps(data))
        except:
            pass

    async def _send_error(self, websocket, message):
        """Send error to player."""
        await self._send_to_player(websocket, {
            "type": "error",
            "message": message
        })


async def main():
    """Start the chess game server."""
    server = ChessGameServer()
    
    print("🎮 Chess Game Server starting...")
    print("🌐 Server will listen on localhost:8765")
    print("📡 Waiting for players to connect...")
    
    async with websockets.serve(server.handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())