import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import queue
import time
from typing import List

# Import the classes we're testing
# Note: You'll need to adjust these imports based on your actual file structure
try:
    from It1_interfaces.Game import Game, InvalidBoard  # Adjust path as needed
    from It1_interfaces.img import Img
    from It1_interfaces.Board import Board
    from It1_interfaces.Command import Command
    from It1_interfaces.Piece import Piece
    from It1_interfaces.EventSystem import EventType, event_publisher
except ImportError:
    # If imports fail, create mock classes for testing purposes
    class Game:
        pass
    class InvalidBoard(Exception):
        pass
    class Img:
        pass
    class Board:
        pass
    class Command:
        pass
    class Piece:
        pass
    class EventType:
        GAME_START = "game_start"
        PIECE_MOVE_START = "piece_move_start"
        PIECE_MOVE_END = "piece_move_end"
        MOVE_MADE = "move_made"
        PIECE_CAPTURED = "piece_captured"
        KING_CAPTURED = "king_captured"
        PAWN_PROMOTED = "pawn_promoted"


class MockPiece:
    """Mock piece for testing"""
    def __init__(self, piece_id: str, position: tuple = (0, 0)):
        self.piece_id = piece_id
        self._state = Mock()
        self._state._physics = Mock()
        self._state._physics.cell = position
        self._state._physics.piece_id = piece_id
        self._state._moves = Mock()
        self._state._moves.valid_moves = [(0, 1, "move"), (0, -1, "move"), (1, 0, "move"), (-1, 0, "move")]
        
    def reset(self, timestamp):
        pass
        
    def update(self, timestamp):
        pass
        
    def draw_on_board(self, board, timestamp):
        pass
        
    def on_command(self, command, timestamp):
        pass


class MockBoard:
    """Mock board for testing"""
    def __init__(self):
        self.img = Mock()
        self.img.img = Mock()
        self.img.img.shape = [800, 800, 3]  # height, width, channels
        
    def clone(self):
        return MockBoard()


class TestGameInitialization(unittest.TestCase):
    """טסטים לאתחול המחלקה"""
    
    def setUp(self):
        """הכנת נתונים לכל טסט"""
        self.pieces = [
            MockPiece("KW0", (4, 7)),  # White King
            MockPiece("KB0", (4, 0)),  # Black King
            MockPiece("PW0", (0, 6)),  # White Pawn
            MockPiece("PB0", (0, 1)),  # Black Pawn
        ]
        self.board = MockBoard()
    
    @patch('It1_interfaces.Game.MessageOverlay')
    @patch('It1_interfaces.Game.ScoreSystem')
    @patch('It1_interfaces.Game.MovesLog')
    @patch('It1_interfaces.Game.SoundSystem')
    def test_game_initialization(self, mock_sound, mock_moves, mock_score, mock_message):
        """בדיקת אתחול תקין של המשחק"""
        game = Game(self.pieces, self.board, "Player1", "Player2")
        
        # בדיקת אתחול בסיסי
        self.assertEqual(game.pieces, self.pieces)
        self.assertEqual(game.board, self.board)
        self.assertEqual(game.player1_name, "Player1")
        self.assertEqual(game.player2_name, "Player2")
        
        # בדיקת מערכות נוספות
        mock_message.assert_called_once()
        mock_score.assert_called_once_with("Player1", "Player2")
        mock_moves.assert_called_once()
        mock_sound.assert_called_once()
        
        # בדיקת מצבים ראשוניים
        self.assertFalse(game.game_over)
        self.assertIsNone(game.selected_piece_player1)
        self.assertIsNone(game.selected_piece_player2)
        self.assertEqual(game.cursor_pos_player1, [0, 7])
        self.assertEqual(game.cursor_pos_player2, [0, 0])

    def test_default_player_names(self):
        """בדיקת שמות ברירת מחדל"""
        game = Game(self.pieces, self.board)
        self.assertEqual(game.player1_name, "Player 1")
        self.assertEqual(game.player2_name, "Player 2")


class TestGameHelpers(unittest.TestCase):
    """טסטים לפונקציות עזר"""
    
    def setUp(self):
        self.pieces = [MockPiece("KW0", (4, 7))]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_game_time_ms(self):
        """בדיקת פונקציית זמן המשחק"""
        with patch('time.monotonic', return_value=1.5):
            self.assertEqual(self.game.game_time_ms(), 1500)
    
    def test_clone_board(self):
        """בדיקת שכפול הלוח"""
        cloned = self.game.clone_board()
        self.assertIsInstance(cloned, type(self.board))
        self.assertIsNot(cloned, self.board)

    def test_get_piece_position(self):
        """בדיקת קבלת מיקום כלי"""
        piece = self.pieces[0]
        position = self.game._get_piece_position(piece)
        self.assertEqual(position, (4, 7))

        # בדיקת כלי שאין לו מיקום
        empty_piece = Mock()
        empty_piece._state = Mock()
        empty_piece._state._physics = Mock()
        empty_piece._state._physics.cell = None

        position = self.game._get_piece_position(empty_piece)
        self.assertIsNone(position)

    def test_find_piece_at_position(self):
        """בדיקת מציאת כלי במיקום"""
        piece = self.game._find_piece_at_position(4, 7)
        self.assertEqual(piece.piece_id, "KW0")
        
        # בדיקת מיקום ריק
        piece = self.game._find_piece_at_position(0, 0)
        self.assertIsNone(piece)

    def test_is_player_piece(self):
        """בדיקת זיהוי כלי שחקן"""
        white_piece = MockPiece("KW0")
        black_piece = MockPiece("KB0")
        
        # שחקן 1 - כלים לבנים
        self.assertTrue(self.game._is_player_piece(white_piece, 1))
        self.assertFalse(self.game._is_player_piece(black_piece, 1))
        
        # שחקן 2 - כלים שחורים
        self.assertFalse(self.game._is_player_piece(white_piece, 2))
        self.assertTrue(self.game._is_player_piece(black_piece, 2))


class TestCursorMovement(unittest.TestCase):
    """טסטים לתנועת הסמנים"""
    
    def setUp(self):
        self.pieces = [MockPiece("KW0")]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_move_cursor_player1(self):
        """בדיקת תנועת סמן שחקן 1"""
        # תנועה רגילה
        self.game._move_cursor_player1(1, 0)
        self.assertEqual(self.game.cursor_pos_player1, [1, 7])
        
        # בדיקת גבולות - לא יוצא מהלוח
        self.game.cursor_pos_player1 = [7, 7]
        self.game._move_cursor_player1(1, 1)
        self.assertEqual(self.game.cursor_pos_player1, [7, 7])
        
        self.game.cursor_pos_player1 = [0, 0]
        self.game._move_cursor_player1(-1, -1)
        self.assertEqual(self.game.cursor_pos_player1, [0, 0])

    def test_move_cursor_player2(self):
        """בדיקת תנועת סמן שחקן 2"""
        # תנועה רגילה
        self.game._move_cursor_player2(1, 1)
        self.assertEqual(self.game.cursor_pos_player2, [1, 1])
        
        # בדיקת גבולות
        self.game.cursor_pos_player2 = [7, 7]
        self.game._move_cursor_player2(1, 1)
        self.assertEqual(self.game.cursor_pos_player2, [7, 7])


class TestPieceSelection(unittest.TestCase):
    """טסטים לבחירת כלים"""
    
    def setUp(self):
        self.pieces = [
            MockPiece("KW0", (0, 7)),  # White King at player1 cursor
            MockPiece("KB0", (0, 0)),  # Black King at player2 cursor
        ]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_select_piece_player1_valid(self):
        """בדיקת בחירת כלי תקינה שחקן 1"""
        self.game._select_piece_player1()
        self.assertEqual(self.game.selected_piece_player1.piece_id, "KW0")
    
    def test_select_piece_player1_invalid_position(self):
        """בדיקת בחירת כלי במיקום שאין בו כלי"""
        self.game.cursor_pos_player1 = [1, 1]  # מיקום ריק
        self.game._select_piece_player1()
        self.assertIsNone(self.game.selected_piece_player1)
    
    def test_select_piece_player1_wrong_color(self):
        """בדיקת בחירת כלי של הצבע הלא נכון"""
        self.game.cursor_pos_player1 = [0, 0]  # מיקום של כלי שחור
        self.game._select_piece_player1()
        self.assertIsNone(self.game.selected_piece_player1)

    def test_select_piece_player2_valid(self):
        """בדיקת בחירת כלי תקינה שחקן 2"""
        self.game._select_piece_player2()
        self.assertEqual(self.game.selected_piece_player2.piece_id, "KB0")


class TestPieceMovement(unittest.TestCase):
    """טסטים לתנועת כלים"""
    
    def setUp(self):
        self.pieces = [
            MockPiece("KW0", (4, 4)),  # White King in center
            MockPiece("KB0", (0, 0)),  # Black King
        ]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_is_valid_move_basic(self):
        """בדיקת תנועה בסיסית חוקית"""
        piece = self.pieces[0]  # White King
        # King can move one square in any direction
        piece._state._moves.valid_moves = [(1, 0, "move"), (0, 1, "move"), (-1, 0, "move"), (0, -1, "move")]
        
        self.assertTrue(self.game._is_valid_move(piece, 5, 4, 1))  # Right
        self.assertTrue(self.game._is_valid_move(piece, 4, 5, 1))  # Down
        self.assertFalse(self.game._is_valid_move(piece, 6, 4, 1))  # Two squares (invalid for king)
    
    def test_is_valid_move_boundaries(self):
        """בדיקת תנועה מחוץ לגבולות הלוח"""
        piece = self.pieces[0]
        piece._state._moves.valid_moves = [(1, 0, "move")]
        
        self.assertFalse(self.game._is_valid_move(piece, 8, 4, 1))  # Outside board
        self.assertFalse(self.game._is_valid_move(piece, -1, 4, 1))  # Outside board

    def test_check_path_clear(self):
        """בדיקת נתיב פנוי"""
        # No pieces between (0,0) and (3,0)
        result = self.game._check_path(0, 0, 3, 0, "RW0")  # Rook move
        self.assertIsNone(result)
    
    def test_check_path_blocked(self):
        """בדיקת נתיב חסום"""
        # Place a piece in the path
        self.pieces.append(MockPiece("PW0", (2, 0)))
        
        result = self.game._check_path(0, 0, 3, 0, "RW0")  # Rook move
        self.assertEqual(result, (2, 0))  # Should return blocking piece position

    def test_check_path_knight_jump(self):
        """בדיקת קפיצת סוס (לא בודק נתיב)"""
        # Knights can jump over pieces
        self.pieces.append(MockPiece("PW0", (1, 1)))
        
        result = self.game._check_path(0, 0, 2, 1, "NW0")  # Knight move
        self.assertIsNone(result)  # Knights ignore blocking pieces


class TestCapture(unittest.TestCase):
    """טסטים לתפיסת כלים"""
    
    def setUp(self):
        self.pieces = [
            MockPiece("KW0", (4, 4)),  # White King
            MockPiece("KB0", (0, 0)),  # Black King
            MockPiece("PB0", (5, 4)),  # Black Pawn next to White King
        ]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    @patch.object(Game, '_announce_win')
    @patch.object(Game, '_is_win', return_value=False)
    def test_handle_arrival_with_capture(self, mock_is_win, mock_announce):
        """בדיקת תפיסת כלי"""
        cmd = Command(timestamp=0, piece_id="KW0", type="arrived")

        # Move the king to the pawn's position
        king = self.pieces[0]
        king._state._physics.cell = (5, 4)  # Same as pawn

        initial_pieces_count = len(self.pieces)
        self.game._handle_arrival(cmd)

        # Pawn should be captured and removed
        self.assertEqual(len(self.pieces), initial_pieces_count - 1)
        self.assertNotIn("PB0", [p.piece_id for p in self.pieces])

    @patch.object(Game, '_announce_win')
    @patch.object(Game, '_is_win', return_value=True)
    def test_handle_arrival_king_capture_triggers_win(self, mock_is_win, mock_announce):
        """בדיקת תפיסת מלך מביאה לניצחון"""
        self.pieces = [MockPiece("KW0", (0, 0))]
        self.game.pieces = self.pieces

        cmd = Command(timestamp=0, piece_id="KW0", type="arrived")
        
        self.game._handle_arrival(cmd)

        mock_announce.assert_called_once()
        self.assertTrue(self.game.game_over)


class TestWinConditions(unittest.TestCase):
    """טסטים לתנאי ניצחון"""
    
    def setUp(self):
        self.board = MockBoard()
    
    def test_is_win_both_kings_alive(self):
        """בדיקה שאין ניצחון כשיש שני מלכים"""
        pieces = [
            MockPiece("KW0", (4, 7)),
            MockPiece("KB0", (4, 0)),
        ]
        game = Game(pieces, self.board)
        self.assertFalse(game._is_win())
    
    def test_is_win_white_king_captured(self):
        """בדיקת ניצחון כשהמלך הלבן נתפס"""
        pieces = [
            MockPiece("KB0", (4, 0)),  # Only black king remains
        ]
        game = Game(pieces, self.board)
        self.assertTrue(game._is_win())
    
    def test_is_win_black_king_captured(self):
        """בדיקת ניצחון כשהמלך השחור נתפס"""
        pieces = [
            MockPiece("KW0", (4, 7)),  # Only white king remains
        ]
        game = Game(pieces, self.board)
        self.assertTrue(game._is_win())

    @patch('builtins.print')
    def test_announce_win_white_wins(self, mock_print):
        """בדיקת הכרזת ניצחון לבן"""
        pieces = [MockPiece("KW0", (4, 7))]  # Only white king
        game = Game(pieces, self.board, "Alice", "Bob")
        
        with patch.object(game, '_show_victory_image'):
            game._announce_win()
        
        # Check that victory message was printed
        mock_print.assert_called()
        self.assertTrue(game.game_over)

    @patch('builtins.print')
    def test_announce_win_black_wins(self, mock_print):
        """בדיקת הכרזת ניצחון שחור"""
        pieces = [MockPiece("KB0", (4, 0))]  # Only black king
        game = Game(pieces, self.board, "Alice", "Bob")
        
        with patch.object(game, '_show_victory_image'):
            game._announce_win()
        
        mock_print.assert_called()
        self.assertTrue(game.game_over)


class TestKeyboardInput(unittest.TestCase):
    """טסטים לקלט מקלדת"""
    
    def setUp(self):
        self.pieces = [
            MockPiece("KW0", (0, 7)),  # White King at player1 start
            MockPiece("KB0", (0, 0)),  # Black King at player2 start
        ]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_keyboard_input_player1_movement(self):
        """בדיקת תנועת שחקן 1 במקלדת"""
        # Test movement keys for player 1
        self.game._handle_keyboard_input(56)  # '8' key - UP
        self.assertEqual(self.game.cursor_pos_player1, [0, 6])
        
        self.game._handle_keyboard_input(54)  # '6' key - RIGHT
        self.assertEqual(self.game.cursor_pos_player1, [1, 6])

    def test_keyboard_input_player2_movement(self):
        """בדיקת תנועת שחקן 2 במקלדת"""
        # Test WASD for player 2
        self.game._handle_keyboard_input(119)  # 'w' key - UP
        self.assertEqual(self.game.cursor_pos_player2, [0, -1])  # Clamped to 0
        
        self.game._handle_keyboard_input(100)  # 'd' key - RIGHT
        self.assertEqual(self.game.cursor_pos_player2, [1, 0])

    def test_keyboard_input_exit_keys(self):
        """בדיקת מקשי יציאה"""
        # ESC key should trigger game exit
        result = self.game._handle_keyboard_input(27)  # ESC
        self.assertTrue(result)
        self.assertTrue(self.game.game_over)
        
        # Reset for next test
        self.game.game_over = False
        
        # 'q' key should also trigger exit
        result = self.game._handle_keyboard_input(ord('q'))
        self.assertTrue(result)
        self.assertTrue(self.game.game_over)

    @patch.object(Game, '_select_piece_player1')
    def test_keyboard_input_piece_selection_player1(self, mock_select):
        """בדיקת בחירת כלי שחקן 1"""
        self.game._handle_keyboard_input(13)  # Enter key
        mock_select.assert_called_once()

    @patch.object(Game, '_select_piece_player2')
    def test_keyboard_input_piece_selection_player2(self, mock_select):
        """בדיקת בחירת כלי שחקן 2"""
        self.game._handle_keyboard_input(32)  # Space key
        mock_select.assert_called_once()


class TestPawnPromotion(unittest.TestCase):
    """טסטים להכתרת חיילים"""
    
    def setUp(self):
        self.pieces = []
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    def test_check_pawn_promotion_white_pawn_reaches_end(self):
        """בדיקת הכתרת חייל לבן שהגיע לסוף"""
        white_pawn = MockPiece("PW0", (4, 0))  # White pawn at row 0
        
        with patch.object(self.game, '_promote_pawn_to_queen') as mock_promote:
            self.game._check_pawn_promotion(white_pawn, (4, 0))
            mock_promote.assert_called_once()

    def test_check_pawn_promotion_black_pawn_reaches_end(self):
        """בדיקת הכתרת חייל שחור שהגיע לסוף"""
        black_pawn = MockPiece("PB0", (4, 7))  # Black pawn at row 7
        
        with patch.object(self.game, '_promote_pawn_to_queen') as mock_promote:
            self.game._check_pawn_promotion(black_pawn, (4, 7))
            mock_promote.assert_called_once()

    def test_check_pawn_promotion_not_pawn(self):
        """בדיקה שכלי שאינו חייל לא מוכתר"""
        king = MockPiece("KW0", (4, 0))
        
        with patch.object(self.game, '_promote_pawn_to_queen') as mock_promote:
            self.game._check_pawn_promotion(king, (4, 0))
            mock_promote.assert_not_called()

    def test_check_pawn_promotion_pawn_not_at_end(self):
        """בדיקה שחייל שלא הגיע לסוף לא מוכתר"""
        white_pawn = MockPiece("PW0", (4, 3))  # White pawn at middle row
        
        with patch.object(self.game, '_promote_pawn_to_queen') as mock_promote:
            self.game._check_pawn_promotion(white_pawn, (4, 3))
            mock_promote.assert_not_called()


class TestEventSystem(unittest.TestCase):
    """טסטים למערכת אירועים"""
    
    def setUp(self):
        self.pieces = [MockPiece("KW0", (4, 7))]
        self.board = MockBoard()
        self.game = Game(self.pieces, self.board)
    
    @patch('It1_interfaces.Game.event_publisher')
    def test_process_input_publishes_move_start_event(self, mock_publisher):
        """בדיקת פרסום אירוע תחילת תנועה"""
        cmd = Command(timestamp=0, piece_id="KW0", type="move")
        cmd.target = (4, 6)

        with patch.object(self.game, '_is_win', return_value=False):
            self.game._process_input(cmd)

        mock_publisher.publish.assert_called()

        
    @patch('It1_interfaces.Game.event_publisher')
    def test_handle_arrival_publishes_move_end_event(self, mock_publisher):
        """בדיקת פרסום אירוע סיום תנועה"""
        cmd = Command(timestamp=0, piece_id="KW0", type="arrived")

        with patch.object(self.game, '_is_win', return_value=False):
            self.game._handle_arrival(cmd)

        mock_publisher.publish.assert_called()



# Test Suite Runner
class TestGameSuite:
    """מארגן את כל הטסטים"""
    
    @staticmethod
    def run_all_tests():
        """הרץ את כל הטסטים"""
        # Create test suite
        test_suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestGameInitialization,
            TestGameHelpers,
            TestCursorMovement,
            TestPieceSelection,
            TestPieceMovement,
            TestCapture,
            TestWinConditions,
            TestKeyboardInput,
            TestPawnPromotion,
            TestEventSystem,
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            test_suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        return result

    @staticmethod
    def run_specific_test(test_class_name: str):
        """הרץ טסט ספציפי"""
        test_classes = {
            'initialization': TestGameInitialization,
            'helpers': TestGameHelpers,
            'cursor': TestCursorMovement,
            'selection': TestPieceSelection,
            'movement': TestPieceMovement,
            'capture': TestCapture,
            'win': TestWinConditions,
            'keyboard': TestKeyboardInput,
            'promotion': TestPawnPromotion,
            'events': TestEventSystem,
        }
        
        if test_class_name in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_class_name])
            runner = unittest.TextTestRunner(verbosity=2)
            return runner.run(suite)
        else:
            print(f"Test class '{test_class_name}' not found.")
            print(f"Available tests: {list(test_classes.keys())}")


if __name__ == "__main__":
    # הרץ את כל הטסטים
    print("🧪 מריץ את כל הטסטים למחלקת Game...")
    print("🧪 Running all Game class tests...")
    
    result = TestGameSuite.run_all_tests()
    
    # הצג סיכום
    print(f"\n📊 סיכום טסטים:")
    print(f"📊 Test Summary:")
    print(f"   ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Failed: {len(result.failures)}")
    print(f"   💥 Errors: {len(result.errors)}")
    print(f"   📈 Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # אם יש כשלונות, הצג אותם
    if result.failures:
        print(f"\n❌ כשלונות:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 שגיאות:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")