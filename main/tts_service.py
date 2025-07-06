"""
Text-to-Speech Service for StorytellerPi
Uses ElevenLabs for high-quality, child-friendly voice synthesis
"""

import os
import io
import logging
import asyncio
import tempfile
from typing import Optional
import pygame

try:
    from elevenlabs import VoiceSettings, generate, save, set_api_key
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logging.warning("ElevenLabs not available")


class TTSService:
    """
    Text-to-Speech service using ElevenLabs
    """
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.logger = logging.getLogger(__name__)
        
        # TTS configuration from environment
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'xsGHrtxT5AdDzYXTQT0d')
        self.model_id = os.getenv('TTS_MODEL_ID', 'eleven_multilingual_v2')
        self.stability = float(os.getenv('TTS_VOICE_STABILITY', '0.75'))
        self.similarity_boost = float(os.getenv('TTS_VOICE_SIMILARITY_BOOST', '0.75'))
        self.voice_speed = float(os.getenv('TTS_VOICE_SPEED', '1.0'))
        
        # Audio playback
        self.audio_output_device = os.getenv('AUDIO_OUTPUT_DEVICE', 'default')
        
        # Initialize services
        self._initialize_elevenlabs()
        self._initialize_pygame()
    
    def _initialize_elevenlabs(self):
        """Initialize ElevenLabs client"""
        try:
            if not ELEVENLABS_AVAILABLE:
                raise ImportError("ElevenLabs library not available")
            
            # Load API key from environment
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if api_key:
                set_api_key(api_key)
                self.logger.info("ElevenLabs API key configured")
            else:
                raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize ElevenLabs: {e}")
            raise
    
    def _initialize_pygame(self):
        """Initialize pygame for audio playback"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.logger.info("Pygame audio initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize pygame: {e}")
            raise    
    async def speak_text(self, text: str, save_audio: bool = False) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to convert to speech
            save_audio: Whether to save audio file for debugging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Converting text to speech: '{text[:50]}...'")
            
            # Generate audio
            audio_data = await self._generate_audio(text)
            if not audio_data:
                return False
            
            # Save to temporary file for playback
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Save audio file if requested
            if save_audio:
                save_path = f"logs/tts_output_{int(asyncio.get_event_loop().time())}.mp3"
                with open(save_path, 'wb') as f:
                    f.write(audio_data)
                self.logger.info(f"Audio saved to: {save_path}")
            
            # Play audio
            success = await self._play_audio(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return success
            
        except Exception as e:
            self.logger.error(f"TTS failed: {e}")
            return False
    
    async def _generate_audio(self, text: str) -> Optional[bytes]:
        """Generate audio using ElevenLabs"""
        try:
            # Configure voice settings
            voice_settings = VoiceSettings(
                stability=self.stability,
                similarity_boost=self.similarity_boost,
                style=0.0,  # Neutral style for children
                use_speaker_boost=True
            )
            
            # Generate audio
            audio = await asyncio.to_thread(
                generate,
                text=text,
                voice=self.voice_id,
                model=self.model_id,
                voice_settings=voice_settings
            )
            
            # Convert to bytes if needed
            if isinstance(audio, bytes):
                return audio
            else:
                # Handle generator or other types
                audio_bytes = b''.join(audio)
                return audio_bytes
                
        except Exception as e:
            self.logger.error(f"ElevenLabs audio generation failed: {e}")
            return None    
    async def _play_audio(self, audio_path: str) -> bool:
        """Play audio file using pygame"""
        try:
            # Load and play audio
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            self.logger.info("Audio playback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio playback failed: {e}")
            return False
    
    def stop_playback(self):
        """Stop current audio playback"""
        try:
            pygame.mixer.music.stop()
            self.logger.info("Audio playback stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop playback: {e}")
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_playback()
            pygame.mixer.quit()
            self.logger.info("TTS service cleaned up")
        except Exception as e:
            self.logger.error(f"TTS cleanup failed: {e}")
    
    async def test_voice(self, test_text: str = "Hello! I'm Elsa, your storytelling friend. Let's have some fun together!") -> bool:
        """Test TTS functionality with a sample phrase"""
        self.logger.info("Testing TTS voice...")
        return await self.speak_text(test_text, save_audio=True)