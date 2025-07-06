#!/usr/bin/env python3
"""
Turkish STT Service - Remote Only
Google Cloud Speech-to-Text API optimized for Turkish language
No local Whisper models - Pi Zero 2W optimized
"""

import os
import sys
import asyncio
import logging
import tempfile
import wave
from typing import Dict, Optional, Any, List
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from google.cloud import speech
    from google.cloud.speech import RecognitionConfig, RecognitionAudio
    import google.auth
    from google.oauth2 import service_account
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    speech = None
    RecognitionConfig = None
    RecognitionAudio = None

try:
    import pyaudio
    import numpy as np
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pyaudio = None
    np = None

class TurkishSTTService:
    """Turkish Speech-to-Text service using Google Cloud Speech API"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.is_initialized = False
        self.audio_interface = None
        
        # Turkish STT configuration
        self.stt_config = {
            'service': os.getenv('STT_SERVICE', 'google'),
            'language_code': os.getenv('STT_LANGUAGE_CODE', 'tr-TR'),
            'alternative_language_codes': [os.getenv('STT_ALTERNATIVE_LANGUAGE', 'tr')],
            'model': os.getenv('STT_MODEL', 'latest_short'),
            'timeout': float(os.getenv('STT_TIMEOUT', '10.0')),
            'max_audio_length': float(os.getenv('STT_MAX_AUDIO_LENGTH', '30.0')),
            'sample_rate': int(os.getenv('STT_SAMPLE_RATE', '16000')),
            'channels': int(os.getenv('STT_CHANNELS', '1')),
            'chunk_size': int(os.getenv('STT_CHUNK_SIZE', '1024')),
            'use_enhanced': True,
            'enable_automatic_punctuation': True,
            'enable_word_time_offsets': False,
            'remote_only': os.getenv('STT_REMOTE_ONLY', 'true').lower() == 'true'
        }
        
        # Google Cloud credentials
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 
                                        '/opt/storytellerpi/credentials/google-credentials.json')
        
        # Audio configuration
        self.audio_config = {
            'sample_rate': self.stt_config['sample_rate'],
            'channels': self.stt_config['channels'],
            'chunk_size': self.stt_config['chunk_size'],
            'format': pyaudio.paInt16 if pyaudio else None
        }
        
        self.logger.info(f"Turkish STT Service initialized - Remote processing only")
    
    async def initialize(self) -> bool:
        """Initialize the Turkish STT service"""
        try:
            self.logger.info("Turkish STT servisi başlatılıyor...")
            
            # Check if required packages are available
            if not GOOGLE_AVAILABLE:
                self.logger.error("Google Cloud Speech kütüphanesi yüklü değil!")
                self.logger.error("Yüklemek için: pip install google-cloud-speech")
                return False
            
            if not AUDIO_AVAILABLE:
                self.logger.error("Ses kütüphaneleri yüklü değil!")
                self.logger.error("Yüklemek için: pip install pyaudio numpy")
                return False
            
            # Check credentials
            if not os.path.exists(self.credentials_path):
                self.logger.error(f"Google credentials dosyası bulunamadı: {self.credentials_path}")
                self.logger.error("Lütfen Google Cloud credentials JSON dosyasını yükleyin")
                return False
            
            # Initialize Google Cloud Speech client
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = speech.SpeechClient(credentials=credentials)
                self.logger.info("✅ Google Cloud Speech client başlatıldı")
            except Exception as e:
                self.logger.error(f"Google Cloud credentials hatası: {e}")
                return False
            
            # Initialize audio interface
            try:
                self.audio_interface = pyaudio.PyAudio()
                self.logger.info("✅ Ses arayüzü başlatıldı")
            except Exception as e:
                self.logger.error(f"Ses arayüzü hatası: {e}")
                return False
            
            # Test connection
            await self._test_connection()
            
            self.is_initialized = True
            self.logger.info("✅ Turkish STT servisi başarıyla başlatıldı!")
            self.logger.info(f"🎤 Dil: {self.stt_config['language_code']}")
            self.logger.info(f"⏱️ Zaman aşımı: {self.stt_config['timeout']} saniye")
            self.logger.info(f"📊 Örnekleme hızı: {self.stt_config['sample_rate']} Hz")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Turkish STT başlatma hatası: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test Google Cloud Speech API connection"""
        try:
            # Create a minimal test recognition request
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.stt_config['sample_rate'],
                language_code=self.stt_config['language_code']
            )
            
            # Create empty audio for test
            audio = RecognitionAudio(content=b'')
            
            # This will fail but confirms API access
            try:
                response = self.client.recognize(config=config, audio=audio)
            except Exception as e:
                # Expected error for empty audio, but confirms API access
                if "audio" in str(e).lower():
                    self.logger.info("✅ Google Cloud Speech API bağlantısı doğrulandı")
                    return True
                else:
                    raise e
            
            return True
            
        except Exception as e:
            self.logger.error(f"Google Cloud Speech API bağlantı testi başarısız: {e}")
            raise
    
    async def record_audio(self, duration: Optional[float] = None) -> bytes:
        """Record audio from microphone"""
        if not self.is_initialized:
            raise RuntimeError("Turkish STT servisi başlatılmamış!")
        
        try:
            duration = duration or self.stt_config['timeout']
            
            self.logger.info(f"Ses kaydı başlatılıyor... {duration} saniye")
            
            # Open audio stream
            stream = self.audio_interface.open(
                format=self.audio_config['format'],
                channels=self.audio_config['channels'],
                rate=self.audio_config['sample_rate'],
                input=True,
                frames_per_buffer=self.audio_config['chunk_size']
            )
            
            frames = []
            frames_to_record = int(self.audio_config['sample_rate'] * duration / self.audio_config['chunk_size'])
            
            self.logger.info("🎤 Ses kaydı başladı - konuşabilirsiniz!")
            
            for _ in range(frames_to_record):
                data = stream.read(self.audio_config['chunk_size'])
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Convert to bytes
            audio_data = b''.join(frames)
            
            self.logger.info(f"✅ Ses kaydı tamamlandı - {len(audio_data)} byte")
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Ses kaydı hatası: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Transcribe audio to Turkish text using Google Cloud Speech"""
        if not self.is_initialized:
            raise RuntimeError("Turkish STT servisi başlatılmamış!")
        
        try:
            self.logger.info("Ses metne dönüştürülüyor...")
            
            # Create recognition configuration
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.stt_config['sample_rate'],
                language_code=self.stt_config['language_code'],
                alternative_language_codes=self.stt_config['alternative_language_codes'],
                model=self.stt_config['model'],
                use_enhanced=self.stt_config['use_enhanced'],
                enable_automatic_punctuation=self.stt_config['enable_automatic_punctuation'],
                enable_word_time_offsets=self.stt_config['enable_word_time_offsets'],
                max_alternatives=3  # Get alternative transcriptions
            )
            
            # Create audio object
            audio = RecognitionAudio(content=audio_data)
            
            # Perform recognition
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.recognize(config=config, audio=audio)
            )
            
            # Process results
            results = []
            main_transcript = ""
            confidence = 0.0
            
            if response.results:
                for result in response.results:
                    alternative = result.alternatives[0]
                    results.append({
                        'transcript': alternative.transcript,
                        'confidence': alternative.confidence,
                        'is_final': True
                    })
                    
                    # Use the first result as main transcript
                    if not main_transcript:
                        main_transcript = alternative.transcript
                        confidence = alternative.confidence
                
                self.logger.info(f"✅ Transkripsiyon tamamlandı: '{main_transcript}'")
                self.logger.info(f"📊 Güven skoru: {confidence:.2f}")
                
            else:
                self.logger.warning("❌ Hiçbir metin tespit edilemedi")
                main_transcript = ""
                confidence = 0.0
            
            return {
                'transcript': main_transcript,
                'confidence': confidence,
                'alternatives': results,
                'language': self.stt_config['language_code'],
                'service': 'google_cloud_speech',
                'processing_time': 0.0  # Google doesn't provide this
            }
            
        except Exception as e:
            self.logger.error(f"Transkripsiyon hatası: {e}")
            raise
    
    async def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio file to Turkish text"""
        if not self.is_initialized:
            raise RuntimeError("Turkish STT servisi başlatılmamış!")
        
        try:
            self.logger.info(f"Dosya transkribsiyonu: {file_path}")
            
            # Read audio file
            with wave.open(file_path, 'rb') as wav_file:
                audio_data = wav_file.readframes(wav_file.getnframes())
            
            # Transcribe
            result = await self.transcribe_audio(audio_data)
            
            self.logger.info(f"✅ Dosya transkribsiyonu tamamlandı")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Dosya transkribsiyon hatası: {e}")
            raise
    
    async def listen_and_transcribe(self, duration: Optional[float] = None) -> Dict[str, Any]:
        """Listen to microphone and transcribe to Turkish text"""
        try:
            self.logger.info("Dinleme ve transkribsiyon başlatılıyor...")
            
            # Record audio
            audio_data = await self.record_audio(duration)
            
            # Transcribe
            result = await self.transcribe_audio(audio_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Dinleme ve transkribsiyon hatası: {e}")
            raise
    
    async def continuous_listen(self, callback, duration: float = 30.0) -> None:
        """Continuous listening with callback for transcription results"""
        if not self.is_initialized:
            raise RuntimeError("Turkish STT servisi başlatılmamış!")
        
        try:
            self.logger.info(f"Sürekli dinleme başlatılıyor... {duration} saniye")
            
            # Open audio stream
            stream = self.audio_interface.open(
                format=self.audio_config['format'],
                channels=self.audio_config['channels'],
                rate=self.audio_config['sample_rate'],
                input=True,
                frames_per_buffer=self.audio_config['chunk_size']
            )
            
            frames = []
            frames_count = 0
            max_frames = int(self.audio_config['sample_rate'] * duration / self.audio_config['chunk_size'])
            
            self.logger.info("🎤 Sürekli dinleme aktif - konuşabilirsiniz!")
            
            try:
                while frames_count < max_frames:
                    data = stream.read(self.audio_config['chunk_size'])
                    frames.append(data)
                    frames_count += 1
                    
                    # Process every 2 seconds
                    if frames_count % (self.audio_config['sample_rate'] // self.audio_config['chunk_size'] * 2) == 0:
                        if frames:
                            audio_data = b''.join(frames)
                            
                            # Check if there's significant audio
                            audio_np = np.frombuffer(audio_data, dtype=np.int16)
                            if np.max(np.abs(audio_np)) > 1000:  # Noise threshold
                                try:
                                    result = await self.transcribe_audio(audio_data)
                                    if result['transcript'].strip():
                                        await callback(result)
                                except Exception as e:
                                    self.logger.error(f"Sürekli dinleme transkribsiyon hatası: {e}")
                            
                            frames = []  # Clear frames for next segment
                            
            finally:
                stream.stop_stream()
                stream.close()
                
        except Exception as e:
            self.logger.error(f"Sürekli dinleme hatası: {e}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return [
            'tr-TR',  # Turkish (Turkey)
            'tr',     # Turkish (generic)
        ]
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'Turkish STT Service',
            'service_provider': 'Google Cloud Speech',
            'language_code': self.stt_config['language_code'],
            'alternative_languages': self.stt_config['alternative_language_codes'],
            'model': self.stt_config['model'],
            'sample_rate': self.stt_config['sample_rate'],
            'timeout': self.stt_config['timeout'],
            'remote_only': self.stt_config['remote_only'],
            'credentials_path': self.credentials_path,
            'credentials_exists': os.path.exists(self.credentials_path),
            'audio_interface_available': self.audio_interface is not None,
            'processing_mode': 'remote_only'
        }
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.audio_interface:
                self.audio_interface.terminate()
            
            self.is_initialized = False
            self.logger.info("Turkish STT servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"STT temizlik hatası: {e}")

# Test function
async def test_turkish_stt():
    """Test the Turkish STT service"""
    print("🎤 Turkish STT Service Test Başlıyor...")
    
    # Initialize service
    stt = TurkishSTTService()
    
    try:
        # Test initialization
        print("📚 Servis başlatılıyor...")
        success = await stt.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Test supported languages
        languages = stt.get_supported_languages()
        print(f"📜 Desteklenen diller: {languages}")
        
        # Test service status
        print("\n📊 Servis durumu:")
        status = stt.get_service_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test audio recording (if available)
        if status['audio_interface_available']:
            print("\n🎤 Ses kaydı testi (5 saniye)...")
            print("Şimdi konuşabilirsiniz...")
            
            try:
                result = await stt.listen_and_transcribe(duration=5.0)
                print(f"✅ Transkribsiyon: '{result['transcript']}'")
                print(f"📊 Güven skoru: {result['confidence']:.2f}")
            except Exception as e:
                print(f"⚠️ Ses kaydı testi atlandı: {e}")
        
        print("\n✅ Test tamamlandı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False
    
    finally:
        await stt.cleanup()

if __name__ == '__main__':
    asyncio.run(test_turkish_stt())