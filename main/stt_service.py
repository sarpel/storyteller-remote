"""
Speech-to-Text Service for StorytellerPi
Supports Google Cloud Speech-to-Text with OpenAI Whisper fallback
"""

import os
import io
import logging
import asyncio
import tempfile
from typing import Optional, Union
import pyaudio
import wave

try:
    from google.cloud import speech
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    GOOGLE_STT_AVAILABLE = False
    logging.warning("Google Cloud Speech not available")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available")


class STTService:
    """
    Speech-to-Text service with multiple provider support
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio configuration
        self.sample_rate = config['audio']['sample_rate']
        self.chunk_size = config['audio']['chunk_size']
        self.channels = config['audio']['channels']
        
        # Initialize clients
        self.google_client = None
        self.openai_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize STT service clients"""
        try:
            # Initialize Google Cloud Speech client
            if GOOGLE_STT_AVAILABLE:
                credentials_path = self.config['apis']['google']['credentials_path']
                if os.path.exists(credentials_path):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                    self.google_client = speech.SpeechClient()
                    self.logger.info("Google Cloud Speech client initialized")
                else:
                    self.logger.warning(f"Google credentials not found: {credentials_path}")
            
            # Initialize OpenAI client
            if OPENAI_AVAILABLE:
                api_key_path = self.config['apis']['openai']['api_key_path']
                if os.path.exists(api_key_path):
                    with open(api_key_path, 'r') as f:
                        api_key = f.read().strip()
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.logger.info("OpenAI client initialized")
                else:
                    self.logger.warning(f"OpenAI API key not found: {api_key_path}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize STT clients: {e}")
    
    async def transcribe_audio(self, audio_data: bytes, use_fallback: bool = True) -> Optional[str]:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Raw audio bytes
            use_fallback: Whether to use OpenAI as fallback if Google fails
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Try Google Cloud Speech first
            if self.google_client:
                result = await self._transcribe_google(audio_data)
                if result:
                    return result
                    
            # Fallback to OpenAI Whisper if enabled
            if use_fallback and self.openai_client:
                self.logger.info("Using OpenAI Whisper as fallback")
                result = await self._transcribe_openai(audio_data)
                if result:
                    return result
                    
            self.logger.error("All STT services failed")
            return None
            
        except Exception as e:
            self.logger.error(f"STT transcription failed: {e}")
            return None    
    async def _transcribe_google(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using Google Cloud Speech-to-Text"""
        try:
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate,
                language_code=self.config['apis']['google']['language_code'],
                audio_channel_count=self.channels,
                enable_automatic_punctuation=True,
            )
            
            # Create audio object
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform recognition
            response = self.google_client.recognize(config=config, audio=audio)
            
            # Extract best result
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                confidence = response.results[0].alternatives[0].confidence
                self.logger.info(f"Google STT result: '{transcript}' (confidence: {confidence})")
                return transcript.strip()
            else:
                self.logger.warning("Google STT returned no results")
                return None
                
        except Exception as e:
            self.logger.error(f"Google STT failed: {e}")
            return None
    
    async def _transcribe_openai(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using OpenAI Whisper"""
        try:
            # Save audio to temporary file (Whisper requires file input)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                self._save_audio_as_wav(audio_data, temp_file.name)
                
                # Transcribe with Whisper
                with open(temp_file.name, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model=self.config['apis']['openai']['model'],
                        file=audio_file,
                        language='en'
                    )
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                if transcript.text:
                    self.logger.info(f"OpenAI Whisper result: '{transcript.text}'")
                    return transcript.text.strip()
                else:
                    self.logger.warning("OpenAI Whisper returned no text")
                    return None
                    
        except Exception as e:
            self.logger.error(f"OpenAI Whisper failed: {e}")
            return None    
    def _save_audio_as_wav(self, audio_data: bytes, filename: str):
        """Save raw audio data as WAV file"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
        except Exception as e:
            self.logger.error(f"Failed to save audio as WAV: {e}")
            raise
    
    def record_audio(self, duration: float = 5.0) -> bytes:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Raw audio bytes
        """
        try:
            audio = pyaudio.PyAudio()
            
            # Find input device
            device_index = None
            if self.config['audio']['input_device'] != "default":
                for i in range(audio.get_device_count()):
                    info = audio.get_device_info_by_index(i)
                    if self.config['audio']['input_device'] in info['name']:
                        device_index = i
                        break
            
            # Open stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            self.logger.info(f"Recording audio for {duration} seconds...")
            
            # Record audio
            frames = []
            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Combine all frames
            audio_data = b''.join(frames)
            self.logger.info(f"Audio recording completed: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Audio recording failed: {e}")
            raise