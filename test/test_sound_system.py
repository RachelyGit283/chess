
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import patch, MagicMock, call
import time

# נניח ש־SoundSystem בקובץ SoundSystem.py בתיקיה הנכונה
from It1_interfaces.SoundSystem import SoundSystem
from It1_interfaces.EventSystem import Event, EventType, event_publisher


class TestSoundSystem(unittest.TestCase):
    def setUp(self):
        # Patch event_publisher.subscribe כדי למנוע רישום אמיתי
        patcher_subscribe = patch('It1_interfaces.SoundSystem.event_publisher.subscribe')
        self.mock_subscribe = patcher_subscribe.start()
        self.addCleanup(patcher_subscribe.stop)

        # יוצרים מופע SoundSystem חדש בכל טסט
        self.sound_system = SoundSystem()

    def test_subscriptions_on_init(self):
        # צריך להירשם לארבעה אירועים
        expected_calls = [
            call(EventType.PIECE_MOVE_START, self.sound_system.on_piece_move_start),
            call(EventType.PIECE_CAPTURED, self.sound_system.on_piece_captured),
            call(EventType.GAME_START, self.sound_system.on_game_start),
            call(EventType.GAME_END, self.sound_system.on_game_end),
            call(EventType.KING_CAPTURED, self.sound_system.on_king_captured),
        ]
        self.mock_subscribe.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(self.mock_subscribe.call_count, 5)

    @patch.object(SoundSystem, '_play_game_start_sound')
    def test_on_game_start_calls_play_sound(self, mock_play):
        event = Event(type=EventType.GAME_START, data={}, timestamp=0)
        self.sound_system.on_game_start(event)
        mock_play.assert_called_once()

    @patch.object(SoundSystem, '_play_game_end_sound')
    def test_on_game_end_calls_play_sound_with_winner(self, mock_play):
        event = Event(type=EventType.GAME_END, data={'winner': 'Player 1'}, timestamp=0)
        self.sound_system.on_game_end(event)
        mock_play.assert_called_once_with('Player 1')

    @patch.object(SoundSystem, '_play_move_sound')
    def test_on_piece_move_start_calls_play_move_sound(self, mock_play):
        event = Event(type=EventType.PIECE_MOVE_START, data={'piece_id': 'PW'}, timestamp=0)
        self.sound_system.on_piece_move_start(event)
        mock_play.assert_called_once_with('PW')

    @patch.object(SoundSystem, '_play_capture_sound')
    def test_on_piece_captured_calls_play_capture_sound(self, mock_play):
        event = Event(type=EventType.PIECE_CAPTURED, data={'captured_piece': 'PW', 'capturing_piece': 'RB'}, timestamp=0)
        self.sound_system.on_piece_captured(event)
        mock_play.assert_called_once_with('PW', 'RB')

    @patch.object(SoundSystem, '_play_king_capture_sound')
    def test_on_king_captured_calls_play_king_capture_sound(self, mock_play):
        event = Event(type=EventType.KING_CAPTURED, data={'king_piece': 'WK'}, timestamp=0)
        self.sound_system.on_king_captured(event)
        mock_play.assert_called_once_with('WK')

    # בדיקות _play_move_sound עם enabled=False
    def test_play_move_sound_disabled(self):
        self.sound_system.enabled = False
        with patch.object(self.sound_system, '_play_tone') as mock_tone, \
             patch.object(self.sound_system, '_play_double_tone') as mock_double, \
             patch.object(self.sound_system, '_play_glide_tone') as mock_glide, \
             patch.object(self.sound_system, '_play_chord') as mock_chord:

            self.sound_system._play_move_sound('PW')
            self.sound_system._play_move_sound('RW')
            self.sound_system._play_move_sound('NW')
            self.sound_system._play_move_sound('BW')
            self.sound_system._play_move_sound('QW')
            self.sound_system._play_move_sound('KW')

            mock_tone.assert_not_called()
            mock_double.assert_not_called()
            mock_glide.assert_not_called()
            mock_chord.assert_not_called()

    # בדיקות _play_move_sound לפי piece_id
    def test_play_move_sound_calls_correct_method(self):
        with patch.object(self.sound_system, '_play_tone') as mock_tone, \
             patch.object(self.sound_system, '_play_double_tone') as mock_double, \
             patch.object(self.sound_system, '_play_glide_tone') as mock_glide, \
             patch.object(self.sound_system, '_play_chord') as mock_chord:

            self.sound_system._play_move_sound('PW')
            mock_tone.assert_called_with(440, 0.1)

            self.sound_system._play_move_sound('RW')
            mock_tone.assert_called_with(220, 0.15)

            self.sound_system._play_move_sound('NW')
            mock_double.assert_called_with(330, 0.08, 0.05)

            self.sound_system._play_move_sound('BW')
            mock_glide.assert_called_with(330, 440, 0.2)

            self.sound_system._play_move_sound('QW')
            mock_chord.assert_called_with([440, 554, 659], 0.2)

            self.sound_system._play_move_sound('KW')
            mock_chord.assert_called_with([220, 277, 330], 0.25)

    # בדיקות _play_capture_sound עם enabled=False
    def test_play_capture_sound_disabled(self):
        self.sound_system.enabled = False
        with patch.object(self.sound_system, '_play_impact_sound') as mock_impact, \
             patch.object(self.sound_system, '_play_king_capture_sound') as mock_king:

            self.sound_system._play_capture_sound('PW', 'RB')
            self.sound_system._play_capture_sound('NW', 'RB')
            self.sound_system._play_capture_sound('RW', 'RB')
            self.sound_system._play_capture_sound('QW', 'RB')
            self.sound_system._play_capture_sound('KW', 'RB')

            mock_impact.assert_not_called()
            mock_king.assert_not_called()

    # בדיקות _play_capture_sound לפי סוגים
    def test_play_capture_sound_calls_correct_method(self):
        with patch.object(self.sound_system, '_play_impact_sound') as mock_impact, \
             patch.object(self.sound_system, '_play_king_capture_sound') as mock_king:

            self.sound_system._play_capture_sound('PW', 'RB')
            mock_impact.assert_called_with(0.1, 400)

            self.sound_system._play_capture_sound('NW', 'RB')
            mock_impact.assert_called_with(0.15, 300)

            self.sound_system._play_capture_sound('BW', 'RB')
            mock_impact.assert_called_with(0.15, 300)

            self.sound_system._play_capture_sound('RW', 'RB')
            mock_impact.assert_called_with(0.2, 250)

            self.sound_system._play_capture_sound('QW', 'RB')
            mock_impact.assert_called_with(0.3, 200)

            self.sound_system._play_capture_sound('KW', 'RB')
            mock_king.assert_called_with('KW')

    # בדיקה ש־_play_king_capture_sound מתנהג נכון עם enabled=False
    def test_play_king_capture_sound_disabled(self):
        self.sound_system.enabled = False
        with patch.object(self.sound_system, '_play_tone') as mock_tone:
            self.sound_system._play_king_capture_sound('KW')
            mock_tone.assert_not_called()

    # בדיקות פומביות _play_king_capture_sound + _play_game_start_sound + _play_game_end_sound
    @patch('time.sleep', return_value=None)
    @patch.object(SoundSystem, '_play_tone')
    def test_play_king_capture_sound_plays_sequence(self, mock_tone, _):
        self.sound_system._play_king_capture_sound('KW')
        # 8 notes, כל אחת עם 0.1 שניות
        self.assertEqual(mock_tone.call_count, 8)

    @patch('time.sleep', return_value=None)
    @patch.object(SoundSystem, '_play_tone')
    def test_play_game_start_sound_plays_sequence(self, mock_tone, _):
        self.sound_system._play_game_start_sound()
        self.assertEqual(mock_tone.call_count, 4)

    @patch.object(SoundSystem, '_play_chord')
    def test_play_game_end_sound_various(self, mock_chord):
        self.sound_system._play_game_end_sound('Player 1')
        mock_chord.assert_called_with([523, 659, 784], 0.5)

        self.sound_system._play_game_end_sound('Player 2')
        mock_chord.assert_called_with([440, 554, 659], 0.5)

    @patch.object(SoundSystem, '_play_tone')
    def test_play_game_end_sound_unknown(self, mock_tone):
        self.sound_system._play_game_end_sound('Draw')
        mock_tone.assert_called_with(440, 0.3)

    # בדיקות הפונקציות הפרטיות _play_tone, _play_double_tone, _play_glide_tone, _play_chord, _play_impact_sound
    @patch('threading.Thread')
    def test_play_tone_starts_thread(self, mock_thread):
        self.sound_system.enabled = True
        self.sound_system._play_tone(440, 0.1)
        self.assertTrue(mock_thread.called)

    @patch('threading.Thread')
    def test_play_double_tone_starts_thread(self, mock_thread):
        self.sound_system.enabled = True
        self.sound_system._play_double_tone(440, 0.1, 0.05)
        self.assertTrue(mock_thread.called)

    @patch('threading.Thread')
    def test_play_glide_tone_starts_thread(self, mock_thread):
        self.sound_system.enabled = True
        self.sound_system._play_glide_tone(440, 880, 0.2)
        self.assertTrue(mock_thread.called)

    @patch('threading.Thread')
    def test_play_chord_starts_thread(self, mock_thread):
        self.sound_system.enabled = True
        self.sound_system._play_chord([440, 550], 0.2)
        self.assertTrue(mock_thread.called)

    @patch('threading.Thread')
    def test_play_impact_sound_starts_thread(self, mock_thread):
        self.sound_system.enabled = True
        self.sound_system._play_impact_sound(0.1, 400)
        self.assertTrue(mock_thread.called)

    # בדיקת הפונקציה _system_beep (פשוט נוודא שהיא לא זורקת)
    def test_system_beep_runs(self):
        try:
            self.sound_system._system_beep()
        except Exception as e:
            self.fail(f"_system_beep raised an exception: {e}")

    # בדיקות set_enabled ומוודאות שינוי הערך
    def test_set_enabled(self):
        self.sound_system.set_enabled(False)
        self.assertFalse(self.sound_system.enabled)
        self.sound_system.set_enabled(True)
        self.assertTrue(self.sound_system.enabled)

    # בדיקות set_volume - כולל גבולות
    def test_set_volume(self):
        self.sound_system.set_volume(0.5)
        self.assertEqual(self.sound_system.volume, 0.5)

        self.sound_system.set_volume(-1)
        self.assertEqual(self.sound_system.volume, 0.0)

        self.sound_system.set_volume(2)
        self.assertEqual(self.sound_system.volume, 1.0)


if __name__ == '__main__':
    unittest.main()
