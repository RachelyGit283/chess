
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

from It1_interfaces.MessageOverlay import MessageOverlay, Message
from It1_interfaces.EventSystem import Event, EventType


class TestMessage(unittest.TestCase):
    def test_default_message_values(self):
        msg = Message(text="Hello", start_time=10.0, duration=3.0)
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(msg.start_time, 10.0)
        self.assertEqual(msg.duration, 3.0)
        self.assertEqual(msg.font_size, 1.0)
        self.assertEqual(msg.color, (255, 255, 255))
        self.assertEqual(msg.background_color, (0, 0, 0, 180))
        self.assertEqual(msg.fade_in_duration, 0.5)
        self.assertEqual(msg.fade_out_duration, 0.5)

    def test_custom_message_values(self):
        msg = Message(
            text="Custom",
            start_time=20.0,
            duration=5.0,
            font_size=2.0,
            color=(0, 255, 0),
            background_color=(10, 20, 30, 100),
            fade_in_duration=1.0,
            fade_out_duration=0.8,
        )
        self.assertEqual(msg.text, "Custom")
        self.assertEqual(msg.duration, 5.0)
        self.assertEqual(msg.color, (0, 255, 0))
        self.assertEqual(msg.background_color, (10, 20, 30, 100))
        self.assertEqual(msg.fade_in_duration, 1.0)
        self.assertEqual(msg.fade_out_duration, 0.8)


class TestMessageOverlay(unittest.TestCase):
    def setUp(self):
        self.mock_event_publisher = Mock()
        patcher = patch('It1_interfaces.MessageOverlay.event_publisher', self.mock_event_publisher)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.time_patcher = patch('It1_interfaces.MessageOverlay.time.time', return_value=100.0)
        self.mock_time = self.time_patcher.start()
        self.addCleanup(self.time_patcher.stop)

        self.overlay = MessageOverlay(duration=2.0)

    def test_overlay_initialization(self):
        self.assertEqual(self.overlay.duration, 2.0)
        self.assertEqual(len(self.overlay.messages), 0)
        self.assertEqual(self.overlay.current_time, 100.0)
        self.assertEqual(self.mock_event_publisher.subscribe.call_count, 4)

    def test_show_basic_message(self):
        self.overlay.show_message("Hello")
        self.assertEqual(len(self.overlay.messages), 1)
        msg = self.overlay.messages[0]
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(msg.duration, 3.0)
        self.assertEqual(msg.start_time, 100.0)

    def test_message_expiry_removal(self):
        self.overlay.show_message("Short", duration=1.0)
        self.overlay.show_message("Long", duration=3.0)

        self.overlay.update(current_time=102.0)  # Short should expire
        self.assertEqual(len(self.overlay.messages), 1)
        self.assertEqual(self.overlay.messages[0].text, "Long")

    def test_clear_messages(self):
        self.overlay.show_message("1")
        self.overlay.show_message("2")
        self.overlay.clear_all_messages()
        self.assertEqual(len(self.overlay.messages), 0)

    def test_has_active_messages(self):
        self.overlay.show_message("Active", duration=2.0)
        with patch('It1_interfaces.MessageOverlay.time.time', return_value=101.0):
            self.assertTrue(self.overlay.has_active_messages())

        with patch('It1_interfaces.MessageOverlay.time.time', return_value=105.0):
            self.assertFalse(self.overlay.has_active_messages())

    @patch('cv2.putText')
    @patch('cv2.addWeighted')
    @patch('cv2.rectangle')
    @patch('cv2.getTextSize')
    def test_draw_on_image_active(self, mock_getTextSize, mock_rectangle, mock_addWeighted, mock_putText):
        mock_getTextSize.return_value = ((100, 20), 5)
        self.overlay.show_message("Draw me", duration=3.0)
        with patch('time.time', return_value=101.0):
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            self.overlay.draw_on_image(img)
            mock_putText.assert_called_once()

    def test_game_start_event(self):
        event = Event(type=EventType.GAME_START, data={'player1_name': 'Alice', 'player2_name': 'Bob'}, timestamp=0)
        self.overlay.on_game_start(event)
        self.assertEqual(len(self.overlay.messages), 6)
        texts = [msg.text for msg in self.overlay.messages]
        self.assertIn("🎮 Chess Game Starting! 🎮", texts)
        self.assertIn("⚪ Alice (White) vs ⚫ Bob (Black)", texts)

    def test_game_end_event(self):
        event = Event(type=EventType.GAME_END, data={'winner': 'Alice', 'reason': 'Checkmate'}, timestamp=0)
        self.overlay.on_game_end(event)
        texts = [msg.text for msg in self.overlay.messages]
        self.assertIn("🏆 Winner: Alice! 🏆", texts)
        self.assertIn("📋 Reason: Checkmate", texts)

    def test_king_capture_event(self):
        event = Event(type=EventType.KING_CAPTURED, data={'king_piece': 'WK', 'capturing_piece': 'BQ'}, timestamp=0)
        self.overlay.on_king_captured(event)
        self.assertEqual(len(self.overlay.messages), 3)
        self.assertIn("⚔️ Black captures White King!", [m.text for m in self.overlay.messages])

    def test_pawn_promoted_event(self):
        event = Event(type=EventType.PAWN_PROMOTED, data={
            'pawn_piece': 'WP', 'new_piece': 'WQ', 'position': (4, 0)
        }, timestamp=0)
        self.overlay.on_pawn_promoted(event)
        self.assertEqual(len(self.overlay.messages), 3)
        self.assertIn("🔥 WP → WQ", [m.text for m in self.overlay.messages])


if __name__ == '__main__':
    unittest.main(verbosity=2)
