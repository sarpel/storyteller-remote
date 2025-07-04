#!/usr/bin/env python3
"""
Audio Feedback Service for StorytellerPi
Provides pleasant audio feedback when wake word is detected or button is pressed
"""

import os
import asyncio
import logging
import numpy as np
import pygame
from typing import Optional
from threading import Thread
import time

logger = logging.getLogger(__name__)


class AudioFeedback:
    """Handles audio feedback for wake word detection and button presses"""
    
    def __init__(self, sample_rate: int = 22050, volume: float = 0.3):
        """
        Initialize audio feedback system
        
        Args:
            sample_rate: Audio sample rate (Hz)
            volume: Feedback volume (0.0 to 1.0)
        """
        self.sample_rate = sample_rate
        self.volume = volume
        self.enabled = True
        
        # Initialize pygame mixer
        try:
            pygame.mixer.pre_init(frequency=sample_rate, size=-16, channels=1, buffer=512)
            pygame.mixer.init()
            logger.info("Audio feedback system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio feedback: {e}")
            self.enabled = False
    
    def generate_chime(self, frequency: float = 800.0, duration: float = 0.25, 
                      fade_in: float = 0.05, fade_out: float = 0.1) -> np.ndarray:
        """
        Generate a pleasant chime sound
        
        Args:
            frequency: Tone frequency in Hz
            duration: Duration in seconds
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            
        Returns:
            Audio data as numpy array
        """
        # Calculate number of samples
        num_samples = int(self.sample_rate * duration)
        
        # Generate time array
        t = np.linspace(0, duration, num_samples, False)
        
        # Generate pure sine wave
        wave = np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in
        fade_in_samples = int(self.sample_rate * fade_in)
        if fade_in_samples > 0:
            fade_in_curve = np.linspace(0, 1, fade_in_samples)
            wave[:fade_in_samples] *= fade_in_curve
        
        # Apply fade out
        fade_out_samples = int(self.sample_rate * fade_out)
        if fade_out_samples > 0:
            fade_out_curve = np.linspace(1, 0, fade_out_samples)
            wave[-fade_out_samples:] *= fade_out_curve
        
        # Apply volume
        wave *= self.volume
        
        # Convert to 16-bit integers
        wave = (wave * 32767).astype(np.int16)
        
        return wave
    
    def generate_success_chime(self) -> np.ndarray:
        """Generate a pleasant success chime (rising tone)"""
        return self.generate_chime(frequency=800.0, duration=0.25)
    
    def generate_button_click(self) -> np.ndarray:
        """Generate a short button click sound"""
        return self.generate_chime(frequency=1000.0, duration=0.15)
    
    def generate_wake_word_chime(self) -> np.ndarray:
        """Generate wake word detection chime"""
        return self.generate_chime(frequency=880.0, duration=0.3)
    
    def generate_error_tone(self) -> np.ndarray:
        """Generate a subtle error tone (lower frequency)"""
        return self.generate_chime(frequency=400.0, duration=0.4)
    
    def play_sound_array(self, sound_array: np.ndarray) -> None:
        """
        Play a sound from numpy array
        
        Args:
            sound_array: Audio data as numpy array
        """
        if not self.enabled:
            return
        
        try:
            # Convert to pygame sound
            sound = pygame.sndarray.make_sound(sound_array)
            
            # Play the sound
            sound.play()
            
            # Wait for sound to finish (non-blocking)
            # pygame.time.wait(int(len(sound_array) / self.sample_rate * 1000))
            
        except Exception as e:
            logger.error(f"Failed to play audio feedback: {e}")
    
    def play_sound_async(self, sound_array: np.ndarray) -> None:
        """Play sound in a separate thread to avoid blocking"""
        if not self.enabled:
            return
        
        def play_thread():
            self.play_sound_array(sound_array)
        
        thread = Thread(target=play_thread, daemon=True)
        thread.start()
    
    def wake_word_detected(self) -> None:
        """Play feedback when wake word is detected"""
        logger.debug("Playing wake word detection feedback")
        chime = self.generate_wake_word_chime()
        self.play_sound_async(chime)
    
    def button_pressed(self) -> None:
        """Play feedback when button is pressed"""
        logger.debug("Playing button press feedback")
        click = self.generate_button_click()
        self.play_sound_async(click)
    
    def success_feedback(self) -> None:
        """Play success feedback"""
        logger.debug("Playing success feedback")
        chime = self.generate_success_chime()
        self.play_sound_async(chime)
    
    def error_feedback(self) -> None:
        """Play error feedback"""
        logger.debug("Playing error feedback")
        tone = self.generate_error_tone()
        self.play_sound_async(tone)
    
    def listening_started(self) -> None:
        """Play feedback when listening starts"""
        self.wake_word_detected()
    
    def listening_stopped(self) -> None:
        """Play feedback when listening stops"""
        # Subtle lower tone to indicate listening stopped
        tone = self.generate_chime(frequency=600.0, duration=0.2)
        self.play_sound_async(tone)
    
    def set_volume(self, volume: float) -> None:
        """Set feedback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Audio feedback volume set to {self.volume}")
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable audio feedback"""
        self.enabled = enabled
        logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")
    
    def test_feedback(self) -> None:
        """Test all feedback sounds"""
        if not self.enabled:
            logger.warning("Audio feedback is disabled")
            return
        
        logger.info("Testing audio feedback sounds...")
        
        # Test wake word chime
        print("Testing wake word chime...")
        self.wake_word_detected()
        time.sleep(0.5)
        
        # Test button click
        print("Testing button click...")
        self.button_pressed()
        time.sleep(0.5)
        
        # Test success chime
        print("Testing success chime...")
        self.success_feedback()
        time.sleep(0.5)
        
        # Test error tone
        print("Testing error tone...")
        self.error_feedback()
        time.sleep(0.5)
        
        logger.info("Audio feedback test completed")
    
    def cleanup(self) -> None:
        """Clean up audio feedback system"""
        try:
            pygame.mixer.quit()
            logger.info("Audio feedback system cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up audio feedback: {e}")


# Global audio feedback instance
_audio_feedback: Optional[AudioFeedback] = None


def get_audio_feedback() -> AudioFeedback:
    """Get the global audio feedback instance"""
    global _audio_feedback
    if _audio_feedback is None:
        # Get configuration from environment
        volume = float(os.getenv('AUDIO_FEEDBACK_VOLUME', '0.3'))
        sample_rate = int(os.getenv('AUDIO_SAMPLE_RATE', '22050'))
        
        _audio_feedback = AudioFeedback(sample_rate=sample_rate, volume=volume)
    
    return _audio_feedback


def initialize_audio_feedback() -> AudioFeedback:
    """Initialize and return audio feedback system"""
    return get_audio_feedback()


def cleanup_audio_feedback() -> None:
    """Clean up audio feedback system"""
    global _audio_feedback
    if _audio_feedback:
        _audio_feedback.cleanup()
        _audio_feedback = None


# Convenience functions for easy use
def play_wake_word_feedback():
    """Play wake word detection feedback"""
    get_audio_feedback().wake_word_detected()


def play_button_feedback():
    """Play button press feedback"""
    get_audio_feedback().button_pressed()


def play_success_feedback():
    """Play success feedback"""
    get_audio_feedback().success_feedback()


def play_error_feedback():
    """Play error feedback"""
    get_audio_feedback().error_feedback()


def play_listening_started():
    """Play listening started feedback"""
    get_audio_feedback().listening_started()


def play_listening_stopped():
    """Play listening stopped feedback"""
    get_audio_feedback().listening_stopped()


if __name__ == "__main__":
    # Test the audio feedback system
    logging.basicConfig(level=logging.INFO)
    
    print("StorytellerPi Audio Feedback Test")
    print("=" * 40)
    
    # Initialize feedback system
    feedback = initialize_audio_feedback()
    
    # Test all sounds
    feedback.test_feedback()
    
    # Cleanup
    cleanup_audio_feedback()
    
    print("Test completed!")