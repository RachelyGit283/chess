# SoundSystem.py - Handles game sounds using system beeps and generated tones
import threading
import time
import math
import numpy as np
try:
    import sounddevice as sd
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("⚠️ sounddevice not available, using system beeps")

import sys
import os
from It1_interfaces.EventSystem import Event, EventType, event_publisher

class SoundSystem:
    """Component that handles game sounds and audio feedback."""
    
    def __init__(self):
        self.enabled = True
        self.volume = 0.3  # Volume level (0.0 to 1.0)
        
        # Subscribe to relevant events
        event_publisher.subscribe(EventType.PIECE_MOVE_START, self.on_piece_move_start)
        event_publisher.subscribe(EventType.PIECE_CAPTURED, self.on_piece_captured)
        event_publisher.subscribe(EventType.GAME_START, self.on_game_start)
        event_publisher.subscribe(EventType.GAME_END, self.on_game_end)
        event_publisher.subscribe(EventType.KING_CAPTURED, self.on_king_captured)
        
        print("🔊 SoundSystem initialized and subscribed to events")
        if not SOUND_AVAILABLE:
            print("🔊 Using system beeps for audio feedback")
    
    def on_game_start(self, event: Event):
        """Play game start sound."""
        self._play_game_start_sound()
        print("🔊 Played game start sound")
    
    def on_game_end(self, event: Event):
        """Play game end sound."""
        winner = event.data.get('winner', 'Unknown')
        self._play_game_end_sound(winner)
        print(f"🔊 Played game end sound for winner: {winner}")
    
    def on_piece_move_start(self, event: Event):
        """Play piece movement sound."""
        piece_id = event.data.get('piece_id', '')
        self._play_move_sound(piece_id)
        print(f"🔊 Played move sound for {piece_id}")
    
    def on_piece_captured(self, event: Event):
        """Play piece capture sound."""
        captured_piece = event.data.get('captured_piece', '')
        capturing_piece = event.data.get('capturing_piece', '')
        self._play_capture_sound(captured_piece, capturing_piece)
        print(f"🔊 Played capture sound: {capturing_piece} captured {captured_piece}")
    
    def on_king_captured(self, event: Event):
        """Play special king capture sound."""
        king_piece = event.data.get('king_piece', '')
        self._play_king_capture_sound(king_piece)
        print(f"🔊 Played king capture sound for {king_piece}")
    
    def _play_move_sound(self, piece_id: str):
        """Play sound when piece starts moving."""
        if not self.enabled:
            return
        
        # Different tones for different pieces
        if piece_id.startswith('P'):  # Pawn - short, light tone
            self._play_tone(440, 0.1)  # A note, 100ms
        elif piece_id.startswith('R'):  # Rook - deep tone
            self._play_tone(220, 0.15)  # A note lower octave, 150ms
        elif piece_id.startswith('N'):  # Knight - galloping rhythm
            self._play_double_tone(330, 0.08, 0.05)  # Quick double tap
        elif piece_id.startswith('B'):  # Bishop - smooth glide
            self._play_glide_tone(330, 440, 0.2)  # Glide up
        elif piece_id.startswith('Q'):  # Queen - regal tone
            self._play_chord([440, 554, 659], 0.2)  # A major chord
        elif piece_id.startswith('K'):  # King - majestic
            self._play_chord([220, 277, 330], 0.25)  # A minor chord, longer
    
    def _play_capture_sound(self, captured_piece: str, capturing_piece: str):
        """Play sound when piece is captured."""
        if not self.enabled:
            return
        
        # Different capture sounds based on captured piece value
        if captured_piece.startswith('P'):  # Captured pawn
            self._play_impact_sound(0.1, 400)
        elif captured_piece.startswith(('N', 'B')):  # Captured minor piece
            self._play_impact_sound(0.15, 300)
        elif captured_piece.startswith('R'):  # Captured rook
            self._play_impact_sound(0.2, 250)
        elif captured_piece.startswith('Q'):  # Captured queen
            self._play_impact_sound(0.3, 200)
        elif captured_piece.startswith('K'):  # Captured king (game end)
            self._play_king_capture_sound(captured_piece)
    
    def _play_king_capture_sound(self, king_piece: str):
        """Play dramatic sound for king capture."""
        if not self.enabled:
            return
        
        # Dramatic descending sequence
        notes = [659, 622, 587, 554, 523, 494, 466, 440]  # E to A descending
        for note in notes:
            self._play_tone(note, 0.1)
            time.sleep(0.05)
    
    def _play_game_start_sound(self):
        """Play sound at game start."""
        if not self.enabled:
            return
        
        # Rising fanfare
        notes = [440, 554, 659, 880]  # A, C#, E, A (octave up)
        for note in notes:
            self._play_tone(note, 0.2)
            time.sleep(0.1)
    
    def _play_game_end_sound(self, winner: str):
        """Play sound at game end."""
        if not self.enabled:
            return
        
        # Victory fanfare or defeat sound
        if "Player 1" in winner or "White" in winner:
            # Victory fanfare for white
            self._play_chord([523, 659, 784], 0.5)  # C major chord
        elif "Player 2" in winner or "Black" in winner:
            # Victory fanfare for black
            self._play_chord([440, 554, 659], 0.5)  # A major chord
        else:
            # Draw or unknown
            self._play_tone(440, 0.3)
    
    def _play_tone(self, frequency: float, duration: float):
        """Play a single tone."""
        if not self.enabled:
            return
        
        def play_async():
            if SOUND_AVAILABLE:
                self._generate_tone(frequency, duration)
            else:
                self._system_beep()
        
        threading.Thread(target=play_async, daemon=True).start()
    
    def _play_double_tone(self, frequency: float, duration1: float, gap: float):
        """Play two quick tones."""
        if not self.enabled:
            return
        
        def play_async():
            if SOUND_AVAILABLE:
                self._generate_tone(frequency, duration1)
                time.sleep(gap)
                self._generate_tone(frequency, duration1)
            else:
                self._system_beep()
                time.sleep(gap)
                self._system_beep()
        
        threading.Thread(target=play_async, daemon=True).start()
    
    def _play_glide_tone(self, start_freq: float, end_freq: float, duration: float):
        """Play a frequency glide."""
        if not self.enabled:
            return
        
        def play_async():
            if SOUND_AVAILABLE:
                self._generate_glide(start_freq, end_freq, duration)
            else:
                self._system_beep()
        
        threading.Thread(target=play_async, daemon=True).start()
    
    def _play_chord(self, frequencies: list, duration: float):
        """Play multiple tones simultaneously (chord)."""
        if not self.enabled:
            return
        
        def play_async():
            if SOUND_AVAILABLE:
                self._generate_chord(frequencies, duration)
            else:
                # Fallback: play tones in sequence
                for freq in frequencies:
                    self._system_beep()
                    time.sleep(0.05)
        
        threading.Thread(target=play_async, daemon=True).start()
    
    def _play_impact_sound(self, duration: float, base_freq: float):
        """Play impact/percussion sound for captures."""
        if not self.enabled:
            return
        
        def play_async():
            if SOUND_AVAILABLE:
                # Generate noise-like impact sound
                sample_rate = 44100
                samples = int(sample_rate * duration)
                
                # Create impact envelope (sharp attack, quick decay)
                t = np.linspace(0, duration, samples)
                envelope = np.exp(-t * 10)  # Quick decay
                
                # Mix of low frequency and noise for impact
                tone = np.sin(2 * np.pi * base_freq * t)
                noise = np.random.normal(0, 0.3, samples)
                sound = (tone * 0.7 + noise * 0.3) * envelope * self.volume
                
                try:
                    sd.play(sound.astype(np.float32), sample_rate)
                except:
                    pass
            else:
                self._system_beep()
        
        threading.Thread(target=play_async, daemon=True).start()
    
    def _generate_tone(self, frequency: float, duration: float):
        """Generate and play a pure tone."""
        try:
            sample_rate = 44100
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            
            # Generate sine wave with fade in/out to avoid clicks
            wave = np.sin(2 * np.pi * frequency * t)
            
            # Apply envelope
            fade_samples = int(samples * 0.1)  # 10% fade
            if fade_samples > 0:
                wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
                wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            wave *= self.volume
            sd.play(wave.astype(np.float32), sample_rate)
            
        except Exception as e:
            print(f"Error playing tone: {e}")
            self._system_beep()
    
    def _generate_glide(self, start_freq: float, end_freq: float, duration: float):
        """Generate frequency glide."""
        try:
            sample_rate = 44100
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            
            # Linear frequency interpolation
            freq_curve = np.linspace(start_freq, end_freq, samples)
            
            # Generate frequency-modulated wave
            phase = np.cumsum(2 * np.pi * freq_curve / sample_rate)
            wave = np.sin(phase) * self.volume
            
            sd.play(wave.astype(np.float32), sample_rate)
            
        except Exception as e:
            print(f"Error playing glide: {e}")
            self._system_beep()
    
    def _generate_chord(self, frequencies: list, duration: float):
        """Generate and play chord (multiple frequencies)."""
        try:
            sample_rate = 44100
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            
            # Mix all frequencies
            wave = np.zeros(samples)
            for freq in frequencies:
                wave += np.sin(2 * np.pi * freq * t) / len(frequencies)
            
            # Apply envelope
            fade_samples = int(samples * 0.1)
            if fade_samples > 0:
                wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
                wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            wave *= self.volume
            sd.play(wave.astype(np.float32), sample_rate)
            
        except Exception as e:
            print(f"Error playing chord: {e}")
            self._system_beep()
    
    def _system_beep(self):
        """Fallback system beep."""
        try:
            if sys.platform.startswith('win'):
                import winsound
                winsound.Beep(440, 200)  # 440Hz for 200ms
            else:
                # Unix/Linux/Mac
                os.system('echo -e "\a"')
        except:
            print("🔊 *beep*")  # Ultimate fallback
    
    def set_enabled(self, enabled: bool):
        """Enable or disable sound."""
        self.enabled = enabled
        print(f"🔊 Sound {'enabled' if enabled else 'disabled'}")
    
    def set_volume(self, volume: float):
        """Set volume level (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        print(f"🔊 Volume set to {self.volume * 100:.0f}%")