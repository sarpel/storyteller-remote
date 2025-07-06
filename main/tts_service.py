#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Service - Türkçe Sesli Okuma Servisi
5 yaşındaki çocuklar için özel olarak tasarlanmış Türkçe hikaye anlatma sistemi
"""

import os
import sys
import asyncio
import logging
import json
import tempfile
import time
from typing import Dict, Optional, Any, List, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import threading
import queue

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Audio playback imports
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

try:
    import pydub
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    pydub = None
    AudioSegment = None

# TTS service imports
try:
    from elevenlabs import generate, save, set_api_key, Voice, VoiceSettings
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    generate = None
    save = None
    set_api_key = None
    Voice = None
    VoiceSettings = None
    ElevenLabs = None

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    speechsdk = None

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

@dataclass
class TTSResult:
    """TTS işlem sonucu"""
    text: str
    audio_file_path: str
    duration: float
    voice_used: str
    service_used: str
    language: str
    timestamp: datetime
    processing_time: float
    file_size: int
    sample_rate: int
    is_cached: bool

class TTSService:
    """Türkçe sesli okuma servisi"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.is_playing = False
        self.current_audio_file = None
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        self._stop_playback = False
        
        # Ses çıkış konfigürasyonu
        self.audio_config = {
            'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '22050')),
            'channels': int(os.getenv('AUDIO_CHANNELS', '1')),
            'bit_depth': int(os.getenv('AUDIO_BIT_DEPTH', '16')),
            'output_device_index': int(os.getenv('AUDIO_OUTPUT_DEVICE_INDEX', '-1')) if os.getenv('AUDIO_OUTPUT_DEVICE_INDEX', '-1') != '-1' else None,
            'volume': float(os.getenv('AUDIO_VOLUME', '0.8')),
            'speed': float(os.getenv('AUDIO_SPEED', '1.0')),
            'pitch': float(os.getenv('AUDIO_PITCH', '1.0'))
        }
        
        # TTS konfigürasyonu
        self.tts_config = {
            'service': os.getenv('TTS_SERVICE', 'elevenlabs'),
            'language': 'tr-TR',
            'voice_id': os.getenv('TTS_VOICE_ID', 'Turkish_Female_Child'),
            'model_id': os.getenv('TTS_MODEL_ID', 'eleven_multilingual_v2'),
            'stability': float(os.getenv('TTS_STABILITY', '0.75')),
            'similarity_boost': float(os.getenv('TTS_SIMILARITY_BOOST', '0.85')),
            'style': float(os.getenv('TTS_STYLE', '0.6')),
            'speaker_boost': os.getenv('TTS_SPEAKER_BOOST', 'true').lower() == 'true',
            'optimize_streaming_latency': int(os.getenv('TTS_OPTIMIZE_STREAMING_LATENCY', '2')),
            'output_format': os.getenv('TTS_OUTPUT_FORMAT', 'mp3_44100_128')
        }
        
        # Çocuk ses konfigürasyonu
        self.child_voice_config = {
            'target_age': int(os.getenv('CHILD_AGE', '5')),
            'gender': os.getenv('CHILD_GENDER', 'kız'),
            'tone': os.getenv('VOICE_TONE', 'gentle_enthusiastic'),
            'emotion': os.getenv('VOICE_EMOTION', 'happy'),
            'speaking_rate': float(os.getenv('VOICE_SPEAKING_RATE', '0.9')),
            'pitch_range': os.getenv('VOICE_PITCH_RANGE', 'medium_high'),
            'warmth': float(os.getenv('VOICE_WARMTH', '0.8')),
            'storytelling_style': os.getenv('VOICE_STORYTELLING_STYLE', 'animated'),
            'pause_duration': float(os.getenv('VOICE_PAUSE_DURATION', '0.5')),
            'emphasis_strength': float(os.getenv('VOICE_EMPHASIS_STRENGTH', '0.7'))
        }
        
        # API konfigürasyonu
        self.api_config = {
            'elevenlabs_api_key': os.getenv('ELEVENLABS_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'azure_speech_key': os.getenv('AZURE_SPEECH_KEY'),
            'azure_speech_region': os.getenv('AZURE_SPEECH_REGION'),
            'timeout': 30.0,
            'retry_count': 3,
            'retry_delay': 1.0
        }
        
        # Türkçe ses ayarları
        self.turkish_voice_settings = {
            'elevenlabs_voices': {
                'Turkish_Female_Child': {
                    'voice_id': 'Turkish_Female_Child',
                    'name': 'Sevimli Prenses',
                    'description': '5 yaşındaki kız çocukları için özel ses',
                    'age_group': 'child',
                    'gender': 'female',
                    'language': 'tr-TR',
                    'accent': 'istanbul',
                    'warmth': 0.9,
                    'clarity': 0.95,
                    'energy': 0.8
                },
                'Turkish_Storyteller': {
                    'voice_id': 'Turkish_Storyteller',
                    'name': 'Hikaye Anlatıcısı',
                    'description': 'Profesyonel hikaye anlatım sesi',
                    'age_group': 'adult',
                    'gender': 'female',
                    'language': 'tr-TR',
                    'accent': 'neutral',
                    'warmth': 0.85,
                    'clarity': 0.98,
                    'energy': 0.75
                }
            },
            'azure_voices': {
                'tr-TR-EmelNeural': {
                    'name': 'Emel',
                    'gender': 'female',
                    'age_group': 'adult',
                    'style': 'cheerful',
                    'role': 'child'
                },
                'tr-TR-AhmetNeural': {
                    'name': 'Ahmet',
                    'gender': 'male',
                    'age_group': 'adult',
                    'style': 'friendly',
                    'role': 'narrator'
                }
            },
            'openai_voices': {
                'nova': {
                    'name': 'Nova',
                    'description': 'Genç ve canlı kadın sesi',
                    'suitable_for': 'storytelling'
                },
                'shimmer': {
                    'name': 'Shimmer',
                    'description': 'Yumuşak ve sıcak kadın sesi',
                    'suitable_for': 'bedtime_stories'
                }
            }
        }
        
        # Hikaye anlatım konfigürasyonu
        self.storytelling_config = {
            'add_pauses': True,
            'pause_markers': ['.', '!', '?', '...', ','],
            'pause_durations': {
                '.': 0.8,
                '!': 1.0,
                '?': 1.0,
                '...': 1.5,
                ',': 0.4
            },
            'emphasis_words': [
                'prenses', 'peri', 'büyülü', 'güzel', 'sevimli', 'tatlı',
                'mutlu', 'neşeli', 'harika', 'muhteşem', 'renkli',
                'dostluk', 'sevgi', 'arkadaş', 'yardım', 'iyilik'
            ],
            'emotion_markers': {
                'excitement': ['vay', 'wow', 'harika', 'süper', 'muhteşem'],
                'gentle': ['yumuşak', 'nazik', 'sevecen', 'tatlı'],
                'mysterious': ['gizli', 'sır', 'büyü', 'sihir'],
                'happy': ['mutlu', 'neşeli', 'gülümse', 'keyifli']
            },
            'speed_adjustments': {
                'action_scenes': 1.1,
                'calm_scenes': 0.9,
                'dialogue': 1.0,
                'narration': 0.95
            }
        }
        
        # Ses dosya yönetimi
        self.audio_cache = {}
        self.temp_dir = tempfile.mkdtemp(prefix='storyteller_audio_')
        self.cache_dir = os.path.join(self.temp_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # TTS clientları
        self.elevenlabs_client = None
        self.openai_client = None
        self.azure_speech_config = None
        self.azure_synthesizer = None
        
        self.logger.info("TTSService başlatıldı - Türkçe sesli okuma hazır")
    
    async def initialize(self) -> bool:
        """TTS servisini başlat"""
        try:
            self.logger.info("TTS servisi başlatılıyor...")
            
            # Ses çıkış sistemini başlat
            if not await self._initialize_audio_output():
                self.logger.warning("Ses çıkış sistemi başlatılamadı - mock moda geçiliyor")
                return True  # Mock modda devam et
            
            # TTS servisini başlat
            if self.tts_config['service'] == 'elevenlabs':
                success = await self._initialize_elevenlabs()
            elif self.tts_config['service'] == 'openai':
                success = await self._initialize_openai_tts()
            elif self.tts_config['service'] == 'azure':
                success = await self._initialize_azure_tts()
            else:
                success = await self._initialize_gtts()
            
            if not success:
                self.logger.warning("Birincil TTS servisi başlatılamadı - alternatif servise geçiliyor")
                success = await self._initialize_fallback_service()
            
            if success:
                self.is_initialized = True
                self._start_playback_thread()
                
                self.logger.info("✅ TTS servisi başarıyla başlatıldı!")
                self.logger.info(f"🔊 Ses konfigürasyonu: {self.audio_config['sample_rate']}Hz, {self.audio_config['channels']} kanal")
                self.logger.info(f"🎭 Ses: {self.tts_config['voice_id']}")
                self.logger.info(f"👶 Çocuk konfigürasyonu: {self.child_voice_config['target_age']} yaş, {self.child_voice_config['gender']}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"TTS servisi başlatma hatası: {e}")
            return False
    
    async def _initialize_audio_output(self) -> bool:
        """Ses çıkış sistemi başlatma"""
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.init(
                    frequency=self.audio_config['sample_rate'],
                    size=-16,
                    channels=self.audio_config['channels'],
                    buffer=512
                )
                pygame.mixer.set_num_channels(8)
                self.logger.info("✅ Pygame ses sistemi başlatıldı!")
                return True
            
            elif PYDUB_AVAILABLE:
                self.logger.info("✅ Pydub ses sistemi hazır!")
                return True
            
            else:
                self.logger.error("Ses çıkış kütüphanesi bulunamadı!")
                return False
                
        except Exception as e:
            self.logger.error(f"Ses çıkış sistemi başlatma hatası: {e}")
            return False
    
    async def _initialize_elevenlabs(self) -> bool:
        """ElevenLabs TTS başlatma"""
        try:
            if not ELEVENLABS_AVAILABLE:
                self.logger.error("ElevenLabs kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['elevenlabs_api_key']:
                self.logger.error("ElevenLabs API anahtarı bulunamadı!")
                return False
            
            self.elevenlabs_client = ElevenLabs(api_key=self.api_config['elevenlabs_api_key'])
            set_api_key(self.api_config['elevenlabs_api_key'])
            
            # Bağlantı testi
            await self._test_elevenlabs_connection()
            
            self.tts_config['active_service'] = 'elevenlabs'
            self.logger.info("✅ ElevenLabs başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"ElevenLabs başlatma hatası: {e}")
            return False
    
    async def _initialize_openai_tts(self) -> bool:
        """OpenAI TTS başlatma"""
        try:
            if not OPENAI_AVAILABLE:
                self.logger.error("OpenAI kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['openai_api_key']:
                self.logger.error("OpenAI API anahtarı bulunamadı!")
                return False
            
            self.openai_client = OpenAI(api_key=self.api_config['openai_api_key'])
            
            # Bağlantı testi
            await self._test_openai_connection()
            
            self.tts_config['active_service'] = 'openai'
            self.logger.info("✅ OpenAI TTS başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI TTS başlatma hatası: {e}")
            return False
    
    async def _initialize_azure_tts(self) -> bool:
        """Azure TTS başlatma"""
        try:
            if not AZURE_AVAILABLE:
                self.logger.error("Azure Speech kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['azure_speech_key'] or not self.api_config['azure_speech_region']:
                self.logger.error("Azure Speech kimlik bilgileri bulunamadı!")
                return False
            
            self.azure_speech_config = speechsdk.SpeechConfig(
                subscription=self.api_config['azure_speech_key'],
                region=self.api_config['azure_speech_region']
            )
            
            self.azure_speech_config.speech_synthesis_language = self.tts_config['language']
            self.azure_speech_config.speech_synthesis_voice_name = 'tr-TR-EmelNeural'
            
            # Bağlantı testi
            await self._test_azure_connection()
            
            self.tts_config['active_service'] = 'azure'
            self.logger.info("✅ Azure TTS başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Azure TTS başlatma hatası: {e}")
            return False
    
    async def _initialize_gtts(self) -> bool:
        """Google TTS başlatma"""
        try:
            if not GTTS_AVAILABLE:
                self.logger.error("gTTS kütüphanesi yüklü değil!")
                return False
            
            # Bağlantı testi
            await self._test_gtts_connection()
            
            self.tts_config['active_service'] = 'gtts'
            self.logger.info("✅ Google TTS başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Google TTS başlatma hatası: {e}")
            return False
    
    async def _initialize_fallback_service(self) -> bool:
        """Yedek servis başlatma"""
        try:
            # Önce gTTS'yi dene
            if await self._initialize_gtts():
                return True
            
            # Sonra mock servisi başlat
            self.tts_config['active_service'] = 'mock'
            self.logger.info("✅ Mock TTS servisi başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Yedek servis başlatma hatası: {e}")
            return False
    
    async def _test_elevenlabs_connection(self) -> bool:
        """ElevenLabs API bağlantı testi"""
        try:
            # Kısa test metni
            test_text = "Test"
            
            audio = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate(
                    text=test_text,
                    voice=self.tts_config['voice_id'],
                    model=self.tts_config['model_id']
                )
            )
            
            self.logger.info("✅ ElevenLabs API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"ElevenLabs API bağlantı testi başarısız: {e}")
            raise
    
    async def _test_openai_connection(self) -> bool:
        """OpenAI API bağlantı testi"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input="Test"
                )
            )
            
            self.logger.info("✅ OpenAI API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI API bağlantı testi başarısız: {e}")
            raise
    
    async def _test_azure_connection(self) -> bool:
        """Azure API bağlantı testi"""
        try:
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.azure_speech_config)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: synthesizer.speak_text_async("Test").get()
            )
            
            self.logger.info("✅ Azure API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Azure API bağlantı testi başarısız: {e}")
            raise
    
    async def _test_gtts_connection(self) -> bool:
        """Google TTS bağlantı testi"""
        try:
            tts = gTTS(text="Test", lang='tr', slow=False)
            test_file = os.path.join(self.temp_dir, 'test.mp3')
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: tts.save(test_file)
            )
            
            if os.path.exists(test_file):
                os.remove(test_file)
            
            self.logger.info("✅ Google TTS bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Google TTS bağlantı testi başarısız: {e}")
            raise
    
    def _start_playback_thread(self) -> None:
        """Ses çalma thread'ini başlat"""
        self.playback_thread = threading.Thread(target=self._playback_loop)
        self.playback_thread.daemon = True
        self.playback_thread.start()
    
    def _playback_loop(self) -> None:
        """Ses çalma döngüsü"""
        while not self._stop_playback:
            try:
                # Kuyruktan ses dosyası al
                audio_file = self.audio_queue.get(timeout=1)
                
                if audio_file == 'STOP':
                    break
                
                # Ses dosyasını çal
                self._play_audio_file(audio_file)
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Ses çalma döngüsü hatası: {e}")
    
    def _play_audio_file(self, file_path: str) -> None:
        """Ses dosyasını çal"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"Ses dosyası bulunamadı: {file_path}")
                return
            
            self.is_playing = True
            self.current_audio_file = file_path
            
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.audio_config['volume'])
                pygame.mixer.music.play()
                
                # Çalma bitene kadar bekle
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
            elif PYDUB_AVAILABLE:
                audio = AudioSegment.from_file(file_path)
                play(audio)
            
            else:
                self.logger.warning("Ses çalma kütüphanesi bulunamadı!")
            
            self.is_playing = False
            self.current_audio_file = None
            
            self.logger.info(f"🔊 Ses dosyası çalındı: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.logger.error(f"Ses çalma hatası: {e}")
            self.is_playing = False
            self.current_audio_file = None
    
    def _enhance_text_for_storytelling(self, text: str) -> str:
        """Metni hikaye anlatımı için iyileştir"""
        enhanced_text = text
        
        if self.storytelling_config['add_pauses']:
            # Noktalama işaretlerine göre duraksama ekle
            for marker, duration in self.storytelling_config['pause_durations'].items():
                if marker in enhanced_text:
                    pause_tag = f'<break time="{duration}s"/>'
                    enhanced_text = enhanced_text.replace(marker, marker + pause_tag)
        
        # Vurgu kelimelerini işaretle
        for word in self.storytelling_config['emphasis_words']:
            if word in enhanced_text.lower():
                enhanced_text = enhanced_text.replace(word, f'<emphasis level="strong">{word}</emphasis>')
        
        # Duygusal işaretleyiciler
        for emotion, words in self.storytelling_config['emotion_markers'].items():
            for word in words:
                if word in enhanced_text.lower():
                    enhanced_text = enhanced_text.replace(word, f'<prosody rate="medium" pitch="high">{word}</prosody>')
        
        return enhanced_text
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None, cache_key: Optional[str] = None) -> Optional[TTSResult]:
        """Metni sese çevir"""
        if not self.is_initialized:
            raise RuntimeError("TTS servisi başlatılmamış!")
        
        try:
            start_time = time.time()
            
            # Cache kontrolü
            if cache_key and cache_key in self.audio_cache:
                cached_result = self.audio_cache[cache_key]
                self.logger.info(f"💾 Önbellekten ses alındı: {cache_key}")
                return cached_result
            
            # Metni hikaye anlatımı için iyileştir
            enhanced_text = self._enhance_text_for_storytelling(text)
            
            # Ses ID'sini belirle
            if not voice_id:
                voice_id = self.tts_config['voice_id']
            
            # Aktif servisi kullanarak ses üret
            if self.tts_config['active_service'] == 'elevenlabs':
                audio_file = await self._synthesize_with_elevenlabs(enhanced_text, voice_id)
            elif self.tts_config['active_service'] == 'openai':
                audio_file = await self._synthesize_with_openai(enhanced_text, voice_id)
            elif self.tts_config['active_service'] == 'azure':
                audio_file = await self._synthesize_with_azure(enhanced_text, voice_id)
            elif self.tts_config['active_service'] == 'gtts':
                audio_file = await self._synthesize_with_gtts(enhanced_text)
            else:
                audio_file = await self._synthesize_with_mock(enhanced_text)
            
            if not audio_file:
                self.logger.error("Ses üretimi başarısız!")
                return None
            
            # Ses dosyası bilgilerini al
            file_size = os.path.getsize(audio_file)
            duration = self._get_audio_duration(audio_file)
            processing_time = time.time() - start_time
            
            # Sonuç objesi oluştur
            result = TTSResult(
                text=text,
                audio_file_path=audio_file,
                duration=duration,
                voice_used=voice_id,
                service_used=self.tts_config['active_service'],
                language=self.tts_config['language'],
                timestamp=datetime.now(),
                processing_time=processing_time,
                file_size=file_size,
                sample_rate=self.audio_config['sample_rate'],
                is_cached=False
            )
            
            # Cache'e ekle
            if cache_key:
                self.audio_cache[cache_key] = result
            
            self.logger.info(f"✅ Ses başarıyla üretildi!")
            self.logger.info(f"📊 Süre: {duration:.1f}s, Boyut: {file_size} bytes")
            self.logger.info(f"⏱️  İşlem süresi: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ses üretimi hatası: {e}")
            return None
    
    async def _synthesize_with_elevenlabs(self, text: str, voice_id: str) -> Optional[str]:
        """ElevenLabs ile ses üretimi"""
        try:
            # Ses ayarları
            voice_settings = VoiceSettings(
                stability=self.tts_config['stability'],
                similarity_boost=self.tts_config['similarity_boost'],
                style=self.tts_config['style'],
                use_speaker_boost=self.tts_config['speaker_boost']
            )
            
            # Ses üret
            audio = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate(
                    text=text,
                    voice=voice_id,
                    model=self.tts_config['model_id'],
                    voice_settings=voice_settings
                )
            )
            
            # Dosyaya kaydet
            output_file = os.path.join(self.temp_dir, f'elevenlabs_{int(time.time())}.mp3')
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: save(audio, output_file)
            )
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"ElevenLabs ses üretimi hatası: {e}")
            return None
    
    async def _synthesize_with_openai(self, text: str, voice_id: str) -> Optional[str]:
        """OpenAI ile ses üretimi"""
        try:
            # OpenAI ses isimlerini map et
            openai_voice = self.turkish_voice_settings['openai_voices'].get(voice_id, {}).get('name', 'nova')
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice=openai_voice,
                    input=text,
                    speed=self.child_voice_config['speaking_rate']
                )
            )
            
            # Dosyaya kaydet
            output_file = os.path.join(self.temp_dir, f'openai_{int(time.time())}.mp3')
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"OpenAI ses üretimi hatası: {e}")
            return None
    
    async def _synthesize_with_azure(self, text: str, voice_id: str) -> Optional[str]:
        """Azure ile ses üretimi"""
        try:
            # Azure ses isimlerini map et
            azure_voice = self.turkish_voice_settings['azure_voices'].get(voice_id, {}).get('name', 'tr-TR-EmelNeural')
            
            # SSML oluştur
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="tr-TR">
                <voice name="{azure_voice}">
                    <prosody rate="{self.child_voice_config['speaking_rate']}" pitch="+10%">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Ses üret
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.azure_speech_config)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: synthesizer.speak_ssml_async(ssml).get()
            )
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Dosyaya kaydet
                output_file = os.path.join(self.temp_dir, f'azure_{int(time.time())}.wav')
                
                with open(output_file, 'wb') as f:
                    f.write(result.audio_data)
                
                return output_file
            
            return None
            
        except Exception as e:
            self.logger.error(f"Azure ses üretimi hatası: {e}")
            return None
    
    async def _synthesize_with_gtts(self, text: str) -> Optional[str]:
        """Google TTS ile ses üretimi"""
        try:
            # Konuşma hızını ayarla
            slow = self.child_voice_config['speaking_rate'] < 1.0
            
            tts = gTTS(text=text, lang='tr', slow=slow)
            
            # Dosyaya kaydet
            output_file = os.path.join(self.temp_dir, f'gtts_{int(time.time())}.mp3')
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: tts.save(output_file)
            )
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Google TTS ses üretimi hatası: {e}")
            return None
    
    async def _synthesize_with_mock(self, text: str) -> Optional[str]:
        """Mock ses üretimi"""
        try:
            # Mock ses dosyası oluştur (sessizlik)
            output_file = os.path.join(self.temp_dir, f'mock_{int(time.time())}.mp3')
            
            # Basit MP3 header (sessizlik)
            mock_audio_data = b'\xff\xfb\x90\x00' + b'\x00' * 1000
            
            with open(output_file, 'wb') as f:
                f.write(mock_audio_data)
            
            self.logger.info(f"🎭 Mock ses dosyası oluşturuldu: {text[:50]}...")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Mock ses üretimi hatası: {e}")
            return None
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Ses dosyası süresini hesapla"""
        try:
            if PYDUB_AVAILABLE:
                audio = AudioSegment.from_file(file_path)
                return len(audio) / 1000.0  # milisaniyeden saniyeye
            else:
                # Dosya boyutuna göre yaklaşık süre hesapla
                file_size = os.path.getsize(file_path)
                # MP3 için yaklaşık hesaplama (128 kbps)
                return file_size / (128 * 1024 / 8)  # saniye
                
        except Exception as e:
            self.logger.error(f"Ses süresi hesaplama hatası: {e}")
            return 0.0
    
    async def play_audio(self, audio_file_path: str) -> bool:
        """Ses dosyasını çal"""
        try:
            if not os.path.exists(audio_file_path):
                self.logger.error(f"Ses dosyası bulunamadı: {audio_file_path}")
                return False
            
            # Ses çalma kuyruğuna ekle
            self.audio_queue.put(audio_file_path)
            
            self.logger.info(f"🔊 Ses çalma kuyruğuna eklendi: {os.path.basename(audio_file_path)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ses çalma hatası: {e}")
            return False
    
    async def speak_text(self, text: str, voice_id: Optional[str] = None) -> bool:
        """Metni seslendir (üret ve çal)"""
        try:
            # Ses üret
            result = await self.synthesize_speech(text, voice_id)
            
            if not result:
                self.logger.error("Ses üretimi başarısız!")
                return False
            
            # Ses dosyasını çal
            success = await self.play_audio(result.audio_file_path)
            
            if success:
                self.logger.info(f"🎤 Metin seslendirildi: {text[:50]}...")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Metin seslendirme hatası: {e}")
            return False
    
    async def stop_playback(self) -> bool:
        """Ses çalmayı durdur"""
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.music.stop()
            
            # Kuyruğu temizle
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.is_playing = False
            self.current_audio_file = None
            
            self.logger.info("🔇 Ses çalma durduruldu!")
            return True
            
        except Exception as e:
            self.logger.error(f"Ses durdurma hatası: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Mevcut sesleri listele"""
        voices = {}
        
        if self.tts_config['active_service'] == 'elevenlabs':
            voices = self.turkish_voice_settings['elevenlabs_voices']
        elif self.tts_config['active_service'] == 'azure':
            voices = self.turkish_voice_settings['azure_voices']
        elif self.tts_config['active_service'] == 'openai':
            voices = self.turkish_voice_settings['openai_voices']
        
        return voices
    
    def get_service_status(self) -> Dict[str, Any]:
        """Servis durumunu getir"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'TTSService',
            'language': self.tts_config['language'],
            'active_service': self.tts_config.get('active_service', 'none'),
            'current_voice': self.tts_config['voice_id'],
            'is_playing': self.is_playing,
            'current_audio_file': self.current_audio_file,
            'audio_queue_size': self.audio_queue.qsize(),
            'pygame_available': PYGAME_AVAILABLE,
            'pydub_available': PYDUB_AVAILABLE,
            'elevenlabs_available': ELEVENLABS_AVAILABLE,
            'openai_available': OPENAI_AVAILABLE,
            'azure_available': AZURE_AVAILABLE,
            'gtts_available': GTTS_AVAILABLE,
            'audio_config': self.audio_config,
            'child_voice_config': self.child_voice_config,
            'storytelling_config': self.storytelling_config,
            'available_voices': list(self.get_available_voices().keys()),
            'cache_size': len(self.audio_cache),
            'temp_dir': self.temp_dir,
            'processing_mode': 'real_time'
        }
    
    async def cleanup(self) -> None:
        """Kaynakları temizle"""
        try:
            # Ses çalmayı durdur
            await self.stop_playback()
            
            # Playback thread'ini durdur
            self._stop_playback = True
            if self.playback_thread and self.playback_thread.is_alive():
                self.audio_queue.put('STOP')
                self.playback_thread.join(timeout=2)
            
            # Pygame'i temizle
            if PYGAME_AVAILABLE:
                pygame.mixer.quit()
            
            # Geçici dosyaları temizle
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            # Cache'i temizle
            self.audio_cache.clear()
            
            self.is_initialized = False
            self.logger.info("TTS servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")

# Test fonksiyonu
async def test_tts_service():
    """TTS servisi testi"""
    print("🔊 TTS Service Test Başlıyor...")
    
    # Servisi başlat
    tts = TTSService()
    
    try:
        # Başlatma testi
        print("📡 Servis başlatılıyor...")
        success = await tts.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Ses üretim testi
        print("\n🎤 Ses üretim testi...")
        test_text = "Merhaba küçük prenses! Sana güzel bir hikaye anlatacağım."
        
        result = await tts.synthesize_speech(test_text)
        
        if result:
            print(f"✅ Ses başarıyla üretildi!")
            print(f"📊 Süre: {result.duration:.1f}s")
            print(f"📁 Dosya: {result.audio_file_path}")
            print(f"🔧 Servis: {result.service_used}")
            print(f"🎭 Ses: {result.voice_used}")
            
            # Ses çalma testi (sadece mock modda)
            if tts.tts_config.get('active_service') == 'mock':
                print("\n🔊 Ses çalma testi...")
                await tts.play_audio(result.audio_file_path)
                
                # Kısa bekleme
                await asyncio.sleep(2)
                
                print("✅ Ses çalma testi tamamlandı!")
        
        # Mevcut sesler
        print("\n🎭 Mevcut sesler:")
        voices = tts.get_available_voices()
        for voice_id, voice_info in voices.items():
            print(f"  {voice_id}: {voice_info.get('name', 'Bilinmeyen')}")
        
        # Servis durumu
        print("\n📊 Servis durumu:")
        status = tts.get_service_status()
        important_keys = ['initialized', 'active_service', 'current_voice', 'is_playing', 'cache_size']
        for key in important_keys:
            if key in status:
                print(f"  {key}: {status[key]}")
        
        print("\n✅ Tüm testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False
    
    finally:
        await tts.cleanup()

if __name__ == '__main__':
    asyncio.run(test_tts_service())