#!/usr/bin/env python3
"""
Turkish TTS Service - Remote Only
ElevenLabs API optimized for Turkish storytelling
Perfect for 5-year-old girl with gentle, storytelling voice
"""

import os
import sys
import asyncio
import logging
import tempfile
import json
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from elevenlabs import generate, voices, set_api_key, Voice, VoiceSettings
    from elevenlabs.api import TTS
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

try:
    import pygame
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pygame = None

class TurkishTTSService:
    """Turkish Text-to-Speech service using ElevenLabs API"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.available_voices = []
        self.selected_voice = None
        
        # Turkish TTS configuration
        self.tts_config = {
            'service': os.getenv('TTS_SERVICE', 'elevenlabs'),
            'language': os.getenv('TTS_LANGUAGE', 'tr'),
            'voice_gender': os.getenv('TTS_VOICE_GENDER', 'female'),
            'voice_age': os.getenv('TTS_VOICE_AGE', 'young_adult'),
            'voice_style': os.getenv('TTS_VOICE_STYLE', 'storyteller'),
            'model_id': os.getenv('TTS_MODEL_ID', 'eleven_turbo_v2'),
            'stability': float(os.getenv('TTS_VOICE_STABILITY', '0.8')),
            'similarity_boost': float(os.getenv('TTS_VOICE_SIMILARITY_BOOST', '0.7')),
            'style': float(os.getenv('TTS_VOICE_STYLE_EXAGGERATION', '0.3')),
            'use_speaker_boost': os.getenv('TTS_USE_SPEAKER_BOOST', 'true').lower() == 'true',
            'optimize_streaming_latency': int(os.getenv('TTS_OPTIMIZE_STREAMING_LATENCY', '2')),
            'output_format': os.getenv('TTS_OUTPUT_FORMAT', 'mp3_44100_128'),
            'remote_only': os.getenv('TTS_REMOTE_ONLY', 'true').lower() == 'true'
        }
        
        # ElevenLabs API configuration
        self.api_config = {
            'api_key': os.getenv('ELEVENLABS_API_KEY'),
            'voice_id': os.getenv('ELEVENLABS_VOICE_ID', 'default_turkish_voice'),
            'base_url': 'https://api.elevenlabs.io/v1',
            'timeout': 30.0
        }
        
        # Child-specific voice settings
        self.child_voice_settings = {
            'stability': self.tts_config['stability'],
            'similarity_boost': self.tts_config['similarity_boost'],
            'style': self.tts_config['style'],
            'use_speaker_boost': self.tts_config['use_speaker_boost']
        }
        
        # Audio playback configuration
        self.audio_config = {
            'sample_rate': 44100,
            'channels': 1,
            'buffer_size': 1024
        }
        
        self.logger.info(f"Turkish TTS Service initialized - Remote ElevenLabs processing")
    
    async def initialize(self) -> bool:
        """Initialize the Turkish TTS service"""
        try:
            self.logger.info("Turkish TTS servisi başlatılıyor...")
            
            # Check if ElevenLabs is available
            if not ELEVENLABS_AVAILABLE:
                self.logger.error("ElevenLabs kütüphanesi yüklü değil!")
                self.logger.error("Yüklemek için: pip install elevenlabs")
                return False
            
            # Check API key
            if not self.api_config['api_key'] or self.api_config['api_key'] == 'YOUR_ELEVENLABS_API_KEY':
                self.logger.error("ElevenLabs API anahtarı bulunamadı!")
                self.logger.error("Lütfen .env dosyasında ELEVENLABS_API_KEY değerini ayarlayın")
                return False
            
            # Set API key
            set_api_key(self.api_config['api_key'])
            
            # Initialize pygame for audio playback
            if AUDIO_AVAILABLE:
                try:
                    pygame.mixer.init(
                        frequency=self.audio_config['sample_rate'],
                        size=-16,
                        channels=self.audio_config['channels'],
                        buffer=self.audio_config['buffer_size']
                    )
                    self.logger.info("✅ Ses oynatma sistemi başlatıldı")
                except Exception as e:
                    self.logger.warning(f"Ses oynatma sistemi uyarısı: {e}")
            
            # Load available voices
            await self._load_voices()
            
            # Select optimal voice for Turkish storytelling
            await self._select_optimal_voice()
            
            # Test connection
            await self._test_connection()
            
            self.is_initialized = True
            self.logger.info("✅ Turkish TTS servisi başarıyla başlatıldı!")
            self.logger.info(f"🎤 Seçilen ses: {self.selected_voice}")
            self.logger.info(f"🎵 Model: {self.tts_config['model_id']}")
            self.logger.info(f"🎭 Stil: {self.tts_config['voice_style']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Turkish TTS başlatma hatası: {e}")
            return False
    
    async def _load_voices(self) -> None:
        """Load available ElevenLabs voices"""
        try:
            self.logger.info("Kullanılabilir sesler yükleniyor...")
            
            # Get voices from ElevenLabs
            voices_response = await asyncio.get_event_loop().run_in_executor(
                None,
                voices
            )
            
            self.available_voices = []
            
            for voice in voices_response:
                voice_info = {
                    'id': voice.voice_id,
                    'name': voice.name,
                    'description': getattr(voice, 'description', ''),
                    'category': getattr(voice, 'category', ''),
                    'language': getattr(voice, 'language', ''),
                    'gender': getattr(voice, 'gender', ''),
                    'age': getattr(voice, 'age', ''),
                    'use_case': getattr(voice, 'use_case', ''),
                    'suitable_for_turkish': self._is_suitable_for_turkish(voice)
                }
                
                self.available_voices.append(voice_info)
            
            self.logger.info(f"✅ {len(self.available_voices)} ses yüklendi")
            
            # Log Turkish-suitable voices
            turkish_voices = [v for v in self.available_voices if v['suitable_for_turkish']]
            self.logger.info(f"🇹🇷 Türkçe için uygun sesler: {len(turkish_voices)}")
            
        except Exception as e:
            self.logger.error(f"Ses yükleme hatası: {e}")
            # Use default voice if loading fails
            self.available_voices = [{
                'id': self.api_config['voice_id'],
                'name': 'Default Turkish Voice',
                'suitable_for_turkish': True
            }]
    
    def _is_suitable_for_turkish(self, voice) -> bool:
        """Check if voice is suitable for Turkish storytelling"""
        # Check if voice supports Turkish or is multilingual
        voice_name = getattr(voice, 'name', '').lower()
        description = getattr(voice, 'description', '').lower()
        language = getattr(voice, 'language', '').lower()
        
        # Turkish indicators
        turkish_indicators = ['turkish', 'türkçe', 'tr', 'multilingual', 'multi-language']
        
        # Storytelling indicators
        storytelling_indicators = ['story', 'narrat', 'child', 'gentle', 'soft', 'calm', 'warm']
        
        # Female voice indicators (preferred for 5-year-old girl)
        female_indicators = ['female', 'woman', 'kadın', 'bayan']
        
        has_turkish = any(indicator in voice_name or indicator in description or indicator in language 
                         for indicator in turkish_indicators)
        
        has_storytelling = any(indicator in voice_name or indicator in description 
                              for indicator in storytelling_indicators)
        
        has_female = any(indicator in voice_name or indicator in description 
                        for indicator in female_indicators)
        
        return has_turkish or (has_storytelling and has_female)
    
    async def _select_optimal_voice(self) -> None:
        """Select the optimal voice for Turkish storytelling"""
        try:
            # If specific voice ID is provided, use it
            if (self.api_config['voice_id'] and 
                self.api_config['voice_id'] != 'default_turkish_voice'):
                self.selected_voice = self.api_config['voice_id']
                self.logger.info(f"🎤 Özel ses seçildi: {self.selected_voice}")
                return
            
            # Find the best Turkish voice
            suitable_voices = [v for v in self.available_voices if v['suitable_for_turkish']]
            
            if suitable_voices:
                # Prefer voices with storytelling characteristics
                storytelling_voices = [v for v in suitable_voices 
                                     if 'story' in v['name'].lower() or 
                                        'narrat' in v['description'].lower() or
                                        'child' in v['description'].lower()]
                
                if storytelling_voices:
                    self.selected_voice = storytelling_voices[0]['id']
                    self.logger.info(f"🎭 Hikaye anlatımı için ses seçildi: {storytelling_voices[0]['name']}")
                else:
                    self.selected_voice = suitable_voices[0]['id']
                    self.logger.info(f"🎤 Türkçe için uygun ses seçildi: {suitable_voices[0]['name']}")
            else:
                # Use default voice
                self.selected_voice = self.available_voices[0]['id'] if self.available_voices else None
                self.logger.warning("⚠️ Varsayılan ses kullanılıyor")
            
        except Exception as e:
            self.logger.error(f"Ses seçimi hatası: {e}")
            self.selected_voice = self.api_config['voice_id']
    
    async def _test_connection(self) -> bool:
        """Test ElevenLabs API connection"""
        try:
            # Test with a simple Turkish phrase
            test_text = "Merhaba, test mesajıdır."
            
            audio_data = await self._generate_audio(test_text)
            
            if len(audio_data) > 1000:  # Reasonable audio size
                self.logger.info("✅ ElevenLabs API bağlantısı başarılı!")
                return True
            else:
                raise Exception("Test sesi çok kısa")
            
        except Exception as e:
            self.logger.error(f"ElevenLabs API bağlantı testi başarısız: {e}")
            raise
    
    async def _generate_audio(self, text: str) -> bytes:
        """Generate audio from text using ElevenLabs"""
        try:
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=self.child_voice_settings['stability'],
                similarity_boost=self.child_voice_settings['similarity_boost'],
                style=self.child_voice_settings['style'],
                use_speaker_boost=self.child_voice_settings['use_speaker_boost']
            )
            
            # Generate audio
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate(
                    text=text,
                    voice=Voice(
                        voice_id=self.selected_voice,
                        settings=voice_settings
                    ),
                    model=self.tts_config['model_id'],
                    optimize_streaming_latency=self.tts_config['optimize_streaming_latency']
                )
            )
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Ses üretimi hatası: {e}")
            raise
    
    async def synthesize_speech(self, text: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Synthesize Turkish speech from text"""
        if not self.is_initialized:
            raise RuntimeError("Turkish TTS servisi başlatılmamış!")
        
        try:
            self.logger.info(f"Metin sese dönüştürülüyor: '{text[:50]}...'")
            
            start_time = datetime.now()
            
            # Generate audio
            audio_data = await self._generate_audio(text)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                self.logger.info(f"💾 Ses dosyası kaydedildi: {output_file}")
            
            # Calculate metrics
            audio_duration = len(audio_data) / (self.audio_config['sample_rate'] * 2)  # Approximate
            
            result = {
                'text': text,
                'audio_data': audio_data,
                'audio_size': len(audio_data),
                'estimated_duration': audio_duration,
                'processing_time': processing_time,
                'voice_id': self.selected_voice,
                'model': self.tts_config['model_id'],
                'language': self.tts_config['language'],
                'output_file': output_file,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Ses üretimi tamamlandı - {len(audio_data)} byte")
            self.logger.info(f"⏱️ İşlem süresi: {processing_time:.2f} saniye")
            self.logger.info(f"🎵 Tahmini süre: {audio_duration:.2f} saniye")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ses sentezi hatası: {e}")
            raise
    
    async def play_audio(self, audio_data: bytes) -> bool:
        """Play audio data through speakers"""
        if not AUDIO_AVAILABLE:
            self.logger.warning("Ses oynatma sistemi mevcut değil")
            return False
        
        try:
            self.logger.info("Ses oynatılıyor...")
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Play audio
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Clean up
            os.unlink(temp_file_path)
            
            self.logger.info("✅ Ses oynatma tamamlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Ses oynatma hatası: {e}")
            return False
    
    async def speak(self, text: str, play_audio: bool = True) -> Dict[str, Any]:
        """Synthesize and optionally play Turkish speech"""
        try:
            # Synthesize speech
            result = await self.synthesize_speech(text)
            
            # Play audio if requested
            if play_audio:
                playback_success = await self.play_audio(result['audio_data'])
                result['played'] = playback_success
            else:
                result['played'] = False
            
            return result
            
        except Exception as e:
            self.logger.error(f"Konuşma hatası: {e}")
            raise
    
    async def speak_story(self, story_text: str, play_audio: bool = True) -> Dict[str, Any]:
        """Speak a story with special storytelling settings"""
        try:
            self.logger.info("📚 Hikaye anlatımı başlatılıyor...")
            
            # Optimize voice settings for storytelling
            original_settings = self.child_voice_settings.copy()
            
            # Storytelling voice settings
            self.child_voice_settings.update({
                'stability': min(self.child_voice_settings['stability'] + 0.1, 1.0),
                'style': min(self.child_voice_settings['style'] + 0.1, 1.0)
            })
            
            try:
                # Synthesize story
                result = await self.speak(story_text, play_audio)
                result['content_type'] = 'story'
                
                self.logger.info("✅ Hikaye anlatımı tamamlandı")
                
                return result
                
            finally:
                # Restore original settings
                self.child_voice_settings = original_settings
            
        except Exception as e:
            self.logger.error(f"Hikaye anlatımı hatası: {e}")
            raise
    
    async def speak_greeting(self, greeting_text: str, play_audio: bool = True) -> Dict[str, Any]:
        """Speak a greeting with warm, welcoming settings"""
        try:
            self.logger.info("👋 Karşılama mesajı...")
            
            # Optimize voice settings for greeting
            original_settings = self.child_voice_settings.copy()
            
            # Greeting voice settings (warmer and more welcoming)
            self.child_voice_settings.update({
                'stability': min(self.child_voice_settings['stability'] + 0.05, 1.0),
                'similarity_boost': min(self.child_voice_settings['similarity_boost'] + 0.05, 1.0)
            })
            
            try:
                # Synthesize greeting
                result = await self.speak(greeting_text, play_audio)
                result['content_type'] = 'greeting'
                
                self.logger.info("✅ Karşılama mesajı tamamlandı")
                
                return result
                
            finally:
                # Restore original settings
                self.child_voice_settings = original_settings
            
        except Exception as e:
            self.logger.error(f"Karşılama mesajı hatası: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available voices"""
        return self.available_voices.copy()
    
    def get_turkish_voices(self) -> List[Dict[str, Any]]:
        """Get voices suitable for Turkish"""
        return [v for v in self.available_voices if v['suitable_for_turkish']]
    
    def set_voice(self, voice_id: str) -> bool:
        """Set the active voice"""
        try:
            # Check if voice exists
            if any(v['id'] == voice_id for v in self.available_voices):
                self.selected_voice = voice_id
                self.logger.info(f"🎤 Ses değiştirildi: {voice_id}")
                return True
            else:
                self.logger.error(f"Ses bulunamadı: {voice_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ses değiştirme hatası: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'Turkish TTS Service',
            'service_provider': 'ElevenLabs',
            'language': self.tts_config['language'],
            'model': self.tts_config['model_id'],
            'selected_voice': self.selected_voice,
            'available_voices_count': len(self.available_voices),
            'turkish_voices_count': len(self.get_turkish_voices()),
            'voice_settings': self.child_voice_settings,
            'audio_available': AUDIO_AVAILABLE,
            'remote_only': self.tts_config['remote_only'],
            'processing_mode': 'remote_only'
        }
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if AUDIO_AVAILABLE:
                pygame.mixer.quit()
            
            self.is_initialized = False
            self.logger.info("Turkish TTS servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"TTS temizlik hatası: {e}")

# Test function
async def test_turkish_tts():
    """Test the Turkish TTS service"""
    print("🎤 Turkish TTS Service Test Başlıyor...")
    
    # Initialize service
    tts = TurkishTTSService()
    
    try:
        # Test initialization
        print("📚 Servis başlatılıyor...")
        success = await tts.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Test available voices
        voices = tts.get_available_voices()
        turkish_voices = tts.get_turkish_voices()
        
        print(f"🎤 Toplam ses sayısı: {len(voices)}")
        print(f"🇹🇷 Türkçe ses sayısı: {len(turkish_voices)}")
        
        for voice in turkish_voices[:3]:  # Show first 3 Turkish voices
            print(f"   - {voice['name']} ({voice['id']})")
        
        # Test service status
        print("\n📊 Servis durumu:")
        status = tts.get_service_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test speech synthesis
        print("\n🎭 Konuşma sentezi testi...")
        test_text = "Merhaba küçük prenses! Bugün sana güzel bir hikaye anlatacağım."
        
        result = await tts.speak(test_text, play_audio=False)
        print(f"✅ Ses üretildi: {result['audio_size']} byte")
        print(f"⏱️ İşlem süresi: {result['processing_time']:.2f} saniye")
        print(f"🎵 Tahmini süre: {result['estimated_duration']:.2f} saniye")
        
        # Test story mode
        print("\n📚 Hikaye modu testi...")
        story_text = "Bir zamanlar, çok uzak diyarlarda güzel bir prenses yaşarmış. Bu prenses çok iyi kalpli ve sevecendi."
        
        story_result = await tts.speak_story(story_text, play_audio=False)
        print(f"✅ Hikaye sesi üretildi: {story_result['audio_size']} byte")
        
        print("\n✅ Tüm testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False
    
    finally:
        await tts.cleanup()

if __name__ == '__main__':
    asyncio.run(test_turkish_tts())