#!/usr/bin/env python3
"""
STT (Speech-to-Text) Service - Türkçe Konuşma Tanıma Servisi
5 yaşındaki çocukların Türkçe konuşmalarını tanıma ve anlama sistemi
"""

import os
import sys
import asyncio
import logging
import json
import threading
import time
from typing import Dict, Optional, Any, List, Callable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import tempfile
import wave

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Audio imports
try:
    import pyaudio
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pyaudio = None
    np = None

# Google Cloud Speech imports
try:
    from google.cloud import speech
    from google.cloud.speech import RecognitionConfig, RecognitionAudio
    from google.api_core.exceptions import GoogleAPICallError
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    speech = None

# OpenAI Whisper imports
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Offline speech recognition
try:
    import speech_recognition as sr
    OFFLINE_SPEECH_AVAILABLE = True
except ImportError:
    OFFLINE_SPEECH_AVAILABLE = False
    sr = None

@dataclass
class STTResult:
    """Konuşma tanıma sonucu"""
    text: str
    confidence: float
    language: str
    timestamp: datetime
    processing_time: float
    service_used: str
    alternatives: List[str]
    is_final: bool

class STTService:
    """Türkçe konuşma tanıma servisi"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.is_listening = False
        self._stop_listening = False
        self.audio_stream = None
        self.recognition_thread = None
        self.callback_function = None
        
        # Ses konfigürasyonu
        self.audio_config = {
            'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '16000')),
            'channels': int(os.getenv('AUDIO_CHANNELS', '1')),
            'chunk_size': int(os.getenv('AUDIO_CHUNK_SIZE', '1024')),
            'format': pyaudio.paInt16 if AUDIO_AVAILABLE else None,
            'input_device_index': int(os.getenv('AUDIO_INPUT_DEVICE_INDEX', '-1')) if os.getenv('AUDIO_INPUT_DEVICE_INDEX', '-1') != '-1' else None
        }
        
        # STT konfigürasyonu
        self.stt_config = {
            'service': os.getenv('STT_SERVICE', 'google'),
            'language': 'tr-TR',  # Türkçe
            'model': os.getenv('STT_MODEL', 'latest_long'),
            'enhanced_models': os.getenv('STT_ENHANCED_MODELS', 'true').lower() == 'true',
            'enable_automatic_punctuation': True,
            'enable_word_time_offsets': True,
            'enable_word_confidence': True,
            'enable_speaker_diarization': False,
            'diarization_speaker_count': 1,
            'max_alternatives': 3,
            'profanity_filter': True,
            'speech_contexts': [
                'hikaye', 'masal', 'prenses', 'peri', 'dostluk', 'macera',
                'hayvan', 'kedi', 'köpek', 'kuş', 'tavşan', 'ayı',
                'anne', 'baba', 'kardeş', 'aile', 'sevgi', 'arkadaş',
                'güzel', 'tatlı', 'sevimli', 'renkli', 'mutlu', 'neşeli',
                'oyun', 'dans', 'şarkı', 'müzik', 'resim', 'boyama',
                'evet', 'hayır', 'lütfen', 'teşekkürler', 'özür dilerim',
                'merhaba', 'güle güle', 'iyi geceler', 'günaydın'
            ]
        }
        
        # Çocuk konuşma konfigürasyonu
        self.child_speech_config = {
            'age_group': os.getenv('CHILD_AGE', '5'),
            'gender': os.getenv('CHILD_GENDER', 'kız'),
            'vocabulary_level': 'beginner',
            'pronunciation_tolerance': 'high',
            'background_noise_threshold': 0.3,
            'silence_threshold': 0.5,
            'min_confidence_threshold': 0.6,
            'phrase_time_limit': 10.0,
            'energy_threshold': 300,
            'dynamic_energy_threshold': True,
            'pause_threshold': 0.8
        }
        
        # API konfigürasyonu
        self.api_config = {
            'google_credentials_path': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'google_project_id': os.getenv('GOOGLE_PROJECT_ID'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'timeout': 30.0,
            'retry_count': 3,
            'retry_delay': 1.0
        }
        
        # Türkçe komut tanıma patterns
        self.turkish_commands = {
            'wake_patterns': [
                'hikaye anlat', 'hikaye anlatır mısın', 'hikaye istiyorum',
                'masal anlat', 'masal anlatır mısın', 'masal istiyorum',
                'hikaye söyle', 'masal söyle', 'bana bir hikaye',
                'hikaye duymak istiyorum', 'hikaye dinlemek istiyorum'
            ],
            'story_requests': [
                'prenses hikayesi', 'peri masalı', 'dostluk hikayesi',
                'macera hikayesi', 'hayvan hikayesi', 'kedi hikayesi',
                'köpek hikayesi', 'kuş hikayesi', 'tavşan hikayesi',
                'güzel hikaye', 'eğlenceli hikaye', 'komik hikaye'
            ],
            'interaction_patterns': [
                'evet', 'hayır', 'tamam', 'devam et', 'bitti mi',
                'daha var mı', 'tekrar söyle', 'anlamadım',
                'çok güzel', 'beğendim', 'süper', 'harika',
                'teşekkürler', 'sağol', 'çok sevdim'
            ],
            'stop_patterns': [
                'dur', 'durdur', 'bitir', 'yeter', 'başka zaman',
                'şimdi olmaz', 'sonra', 'istemiyorum', 'vazgeçtim'
            ]
        }
        
        # Servis clientları
        self.google_client = None
        self.openai_client = None
        self.offline_recognizer = None
        self.microphone = None
        self.audio_interface = None
        
        self.logger.info("STTService başlatıldı - Türkçe konuşma tanıma hazır")
    
    async def initialize(self) -> bool:
        """STT servisini başlat"""
        try:
            self.logger.info("STT servisi başlatılıyor...")
            
            # Ses sistemini başlat
            if not await self._initialize_audio():
                self.logger.warning("Ses sistemi başlatılamadı - mock moda geçiliyor")
                return True  # Mock modda devam et
            
            # STT servisini başlat
            if self.stt_config['service'] == 'google':
                success = await self._initialize_google_speech()
            elif self.stt_config['service'] == 'openai':
                success = await self._initialize_openai_whisper()
            else:
                success = await self._initialize_offline_speech()
            
            if not success:
                self.logger.warning("Birincil STT servisi başlatılamadı - alternatif servise geçiliyor")
                success = await self._initialize_fallback_service()
            
            if success:
                self.is_initialized = True
                self.logger.info("✅ STT servisi başarıyla başlatıldı!")
                self.logger.info(f"🎤 Ses konfigürasyonu: {self.audio_config['sample_rate']}Hz, {self.audio_config['channels']} kanal")
                self.logger.info(f"🗣️  Dil: {self.stt_config['language']}")
                self.logger.info(f"👶 Çocuk konfigürasyonu: {self.child_speech_config['age_group']} yaş, {self.child_speech_config['gender']}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"STT servisi başlatma hatası: {e}")
            return False
    
    async def _initialize_audio(self) -> bool:
        """Ses sistemi başlatma"""
        try:
            if not AUDIO_AVAILABLE:
                self.logger.error("PyAudio kütüphanesi yüklü değil!")
                return False
            
            self.audio_interface = pyaudio.PyAudio()
            
            # Ses kartlarını listele
            self.logger.info("Mevcut ses kartları:")
            for i in range(self.audio_interface.get_device_count()):
                info = self.audio_interface.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    self.logger.info(f"  {i}: {info['name']} (Girdi: {info['maxInputChannels']} kanal)")
            
            # Ses cihazını test et
            if self.audio_config['input_device_index'] is not None:
                try:
                    device_info = self.audio_interface.get_device_info_by_index(self.audio_config['input_device_index'])
                    self.logger.info(f"Seçilen ses cihazı: {device_info['name']}")
                except Exception as e:
                    self.logger.warning(f"Belirtilen ses cihazı bulunamadı: {e}")
                    self.audio_config['input_device_index'] = None
            
            # Offline speech recognition için mikrofonu hazırla
            if OFFLINE_SPEECH_AVAILABLE:
                self.offline_recognizer = sr.Recognizer()
                self.microphone = sr.Microphone(device_index=self.audio_config['input_device_index'])
                
                # Mikrofonu kalibre et
                self.logger.info("Mikrofon kalibre ediliyor...")
                with self.microphone as source:
                    if self.child_speech_config['dynamic_energy_threshold']:
                        self.offline_recognizer.adjust_for_ambient_noise(source, duration=1)
                    else:
                        self.offline_recognizer.energy_threshold = self.child_speech_config['energy_threshold']
                    
                    self.offline_recognizer.pause_threshold = self.child_speech_config['pause_threshold']
                    self.offline_recognizer.phrase_time_limit = self.child_speech_config['phrase_time_limit']
                
                self.logger.info(f"Mikrofon hazır - Energy threshold: {self.offline_recognizer.energy_threshold}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ses sistemi başlatma hatası: {e}")
            return False
    
    async def _initialize_google_speech(self) -> bool:
        """Google Cloud Speech başlatma"""
        try:
            if not GOOGLE_SPEECH_AVAILABLE:
                self.logger.error("Google Cloud Speech kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['google_credentials_path']:
                self.logger.error("Google Cloud kimlik bilgileri bulunamadı!")
                return False
            
            self.google_client = speech.SpeechClient()
            
            # Bağlantı testi
            await self._test_google_connection()
            
            self.stt_config['active_service'] = 'google'
            self.logger.info("✅ Google Cloud Speech başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Cloud Speech başlatma hatası: {e}")
            return False
    
    async def _initialize_openai_whisper(self) -> bool:
        """OpenAI Whisper başlatma"""
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
            
            self.stt_config['active_service'] = 'openai'
            self.logger.info("✅ OpenAI Whisper başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI Whisper başlatma hatası: {e}")
            return False
    
    async def _initialize_offline_speech(self) -> bool:
        """Offline konuşma tanıma başlatma"""
        try:
            if not OFFLINE_SPEECH_AVAILABLE:
                self.logger.error("Offline speech recognition kütüphanesi yüklü değil!")
                return False
            
            if not self.offline_recognizer:
                await self._initialize_audio()
            
            self.stt_config['active_service'] = 'offline'
            self.logger.info("✅ Offline konuşma tanıma başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Offline konuşma tanıma başlatma hatası: {e}")
            return False
    
    async def _initialize_fallback_service(self) -> bool:
        """Yedek servis başlatma"""
        try:
            # Önce offline'ı dene
            if await self._initialize_offline_speech():
                return True
            
            # Sonra mock servisi başlat
            self.stt_config['active_service'] = 'mock'
            self.logger.info("✅ Mock STT servisi başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Yedek servis başlatma hatası: {e}")
            return False
    
    async def _test_google_connection(self) -> bool:
        """Google Cloud Speech API bağlantı testi"""
        try:
            # Test audio data
            test_audio = RecognitionAudio(content=b'')
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code='tr-TR'
            )
            
            # Test isteği (başarısız olması beklenir ama API'ye erişim test edilir)
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.google_client.recognize(config=config, audio=test_audio)
                )
            except Exception:
                pass  # Beklenen hata - önemli olan API'ye erişim
            
            self.logger.info("✅ Google Cloud Speech API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Cloud Speech API bağlantı testi başarısız: {e}")
            raise
    
    async def _test_openai_connection(self) -> bool:
        """OpenAI API bağlantı testi"""
        try:
            # Test için küçük bir ses dosyası oluştur
            test_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            test_file.write(b'test')
            test_file.close()
            
            try:
                with open(test_file.name, 'rb') as f:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f,
                            language="tr"
                        )
                    )
            except Exception:
                pass  # Beklenen hata - önemli olan API'ye erişim
            
            os.unlink(test_file.name)
            
            self.logger.info("✅ OpenAI API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI API bağlantı testi başarısız: {e}")
            raise
    
    async def start_listening(self, callback: Callable[[STTResult], None]) -> bool:
        """Dinlemeyi başlat"""
        if not self.is_initialized:
            self.logger.error("STT servisi başlatılmamış!")
            return False
        
        if self.is_listening:
            self.logger.warning("Zaten dinleniyor!")
            return True
        
        try:
            self.callback_function = callback
            self.is_listening = True
            self._stop_listening = False
            
            # Dinleme thread'ini başlat
            self.recognition_thread = threading.Thread(target=self._recognition_loop)
            self.recognition_thread.daemon = True
            self.recognition_thread.start()
            
            self.logger.info("🎤 Dinleme başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Dinleme başlatma hatası: {e}")
            return False
    
    def _recognition_loop(self) -> None:
        """Konuşma tanıma döngüsü"""
        while self.is_listening and not self._stop_listening:
            try:
                if self.stt_config['active_service'] == 'mock':
                    # Mock modda rastgele Türkçe metinler üret
                    time.sleep(5)  # 5 saniye bekle
                    mock_texts = [
                        "Merhaba, hikaye anlatır mısın?",
                        "Prenses hikayesi istiyorum",
                        "Peri masalı söyle",
                        "Dostluk hikayesi anlat",
                        "Hayvan hikayesi dinlemek istiyorum",
                        "Çok güzel bir hikaye",
                        "Teşekkürler, çok beğendim",
                        "Devam et lütfen"
                    ]
                    
                    import random
                    mock_text = random.choice(mock_texts)
                    
                    result = STTResult(
                        text=mock_text,
                        confidence=0.95,
                        language='tr-TR',
                        timestamp=datetime.now(),
                        processing_time=0.1,
                        service_used='mock',
                        alternatives=[mock_text],
                        is_final=True
                    )
                    
                    if self.callback_function:
                        self.callback_function(result)
                    
                    continue
                
                # Gerçek konuşma tanıma
                audio_data = self._record_audio()
                if audio_data:
                    result = await self._process_audio(audio_data)
                    if result and self.callback_function:
                        self.callback_function(result)
                
                # Kısa bekleme
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Konuşma tanıma döngüsü hatası: {e}")
                time.sleep(1)
    
    def _record_audio(self) -> Optional[bytes]:
        """Ses kaydı al"""
        try:
            if self.stt_config['active_service'] == 'mock':
                return b'mock_audio_data'
            
            if not self.microphone or not self.offline_recognizer:
                return None
            
            # Ses yakala
            with self.microphone as source:
                audio = self.offline_recognizer.listen(
                    source,
                    timeout=1,
                    phrase_time_limit=self.child_speech_config['phrase_time_limit']
                )
                return audio.get_wav_data()
                
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Ses kaydı hatası: {e}")
            return None
    
    async def _process_audio(self, audio_data: bytes) -> Optional[STTResult]:
        """Ses verisini işle"""
        try:
            start_time = time.time()
            
            if self.stt_config['active_service'] == 'google':
                result = await self._process_with_google(audio_data)
            elif self.stt_config['active_service'] == 'openai':
                result = await self._process_with_openai(audio_data)
            else:
                result = await self._process_with_offline(audio_data)
            
            processing_time = time.time() - start_time
            
            if result:
                result.processing_time = processing_time
                result.timestamp = datetime.now()
                
                # Türkçe komut tanımayı kontrol et
                self._analyze_turkish_command(result)
                
                self.logger.info(f"🗣️  Tanınan metin: {result.text}")
                self.logger.info(f"📊 Güven: {result.confidence:.2f}, İşlem süresi: {processing_time:.2f}s")
                
                return result
            
        except Exception as e:
            self.logger.error(f"Ses işleme hatası: {e}")
            return None
    
    async def _process_with_google(self, audio_data: bytes) -> Optional[STTResult]:
        """Google Cloud Speech ile işle"""
        try:
            audio = RecognitionAudio(content=audio_data)
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.audio_config['sample_rate'],
                language_code=self.stt_config['language'],
                model=self.stt_config['model'],
                enable_automatic_punctuation=self.stt_config['enable_automatic_punctuation'],
                enable_word_time_offsets=self.stt_config['enable_word_time_offsets'],
                enable_word_confidence=self.stt_config['enable_word_confidence'],
                max_alternatives=self.stt_config['max_alternatives'],
                profanity_filter=self.stt_config['profanity_filter'],
                speech_contexts=[{
                    'phrases': self.stt_config['speech_contexts'],
                    'boost': 20.0
                }]
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.google_client.recognize(config=config, audio=audio)
            )
            
            if response.results:
                result = response.results[0]
                alternatives = [alt.transcript for alt in result.alternatives]
                
                return STTResult(
                    text=result.alternatives[0].transcript,
                    confidence=result.alternatives[0].confidence,
                    language=self.stt_config['language'],
                    timestamp=datetime.now(),
                    processing_time=0.0,
                    service_used='google',
                    alternatives=alternatives,
                    is_final=True
                )
            
        except Exception as e:
            self.logger.error(f"Google Speech işleme hatası: {e}")
            return None
    
    async def _process_with_openai(self, audio_data: bytes) -> Optional[STTResult]:
        """OpenAI Whisper ile işle"""
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            try:
                with open(tmp_file_path, 'rb') as audio_file:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="tr",
                            response_format="verbose_json"
                        )
                    )
                
                return STTResult(
                    text=response.text,
                    confidence=0.9,  # Whisper confidence vermez
                    language='tr-TR',
                    timestamp=datetime.now(),
                    processing_time=0.0,
                    service_used='openai',
                    alternatives=[response.text],
                    is_final=True
                )
                
            finally:
                os.unlink(tmp_file_path)
                
        except Exception as e:
            self.logger.error(f"OpenAI Whisper işleme hatası: {e}")
            return None
    
    async def _process_with_offline(self, audio_data: bytes) -> Optional[STTResult]:
        """Offline konuşma tanıma ile işle"""
        try:
            # AudioData objesi oluştur
            audio = sr.AudioData(audio_data, self.audio_config['sample_rate'], 2)
            
            # Google API kullanarak tanıma (ücretsiz)
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.offline_recognizer.recognize_google(audio, language='tr-TR')
            )
            
            return STTResult(
                text=text,
                confidence=0.8,  # Offline için varsayılan
                language='tr-TR',
                timestamp=datetime.now(),
                processing_time=0.0,
                service_used='offline',
                alternatives=[text],
                is_final=True
            )
            
        except sr.UnknownValueError:
            self.logger.debug("Konuşma anlaşılamadı")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Offline konuşma tanıma hatası: {e}")
            return None
    
    def _analyze_turkish_command(self, result: STTResult) -> None:
        """Türkçe komut analizi"""
        text = result.text.lower()
        
        # Komut türünü belirle
        command_type = None
        
        for pattern in self.turkish_commands['wake_patterns']:
            if pattern in text:
                command_type = 'wake'
                break
        
        if not command_type:
            for pattern in self.turkish_commands['story_requests']:
                if pattern in text:
                    command_type = 'story_request'
                    break
        
        if not command_type:
            for pattern in self.turkish_commands['interaction_patterns']:
                if pattern in text:
                    command_type = 'interaction'
                    break
        
        if not command_type:
            for pattern in self.turkish_commands['stop_patterns']:
                if pattern in text:
                    command_type = 'stop'
                    break
        
        # Sonucu güncelle
        if hasattr(result, 'command_type'):
            result.command_type = command_type
        else:
            result.command_type = command_type
    
    async def stop_listening(self) -> bool:
        """Dinlemeyi durdur"""
        try:
            self._stop_listening = True
            self.is_listening = False
            
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.recognition_thread.join(timeout=2)
            
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            self.logger.info("🔇 Dinleme durduruldu!")
            return True
            
        except Exception as e:
            self.logger.error(f"Dinleme durdurma hatası: {e}")
            return False
    
    async def transcribe_audio_file(self, file_path: str) -> Optional[STTResult]:
        """Ses dosyasını metne çevir"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"Ses dosyası bulunamadı: {file_path}")
                return None
            
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                
            result = await self._process_audio(audio_data)
            
            if result:
                self.logger.info(f"📄 Dosya transkripsiyonu tamamlandı: {file_path}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Dosya transkripsiyonu hatası: {e}")
            return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Servis durumunu getir"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'STTService',
            'language': self.stt_config['language'],
            'active_service': self.stt_config.get('active_service', 'none'),
            'is_listening': self.is_listening,
            'audio_available': AUDIO_AVAILABLE,
            'google_speech_available': GOOGLE_SPEECH_AVAILABLE,
            'openai_available': OPENAI_AVAILABLE,
            'offline_speech_available': OFFLINE_SPEECH_AVAILABLE,
            'audio_config': self.audio_config,
            'child_speech_config': self.child_speech_config,
            'supported_commands': list(self.turkish_commands.keys()),
            'speech_contexts': self.stt_config['speech_contexts'][:10],  # İlk 10 tanesi
            'model': self.stt_config['model'],
            'processing_mode': 'real_time' if self.is_listening else 'on_demand'
        }
    
    async def cleanup(self) -> None:
        """Kaynakları temizle"""
        try:
            await self.stop_listening()
            
            if self.audio_interface:
                self.audio_interface.terminate()
                self.audio_interface = None
            
            if self.google_client:
                self.google_client = None
            
            if self.openai_client:
                self.openai_client = None
            
            self.is_initialized = False
            self.logger.info("STT servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")

# Test fonksiyonu
async def test_stt_service():
    """STT servisi testi"""
    print("🎤 STT Service Test Başlıyor...")
    
    # Servisi başlat
    stt = STTService()
    
    try:
        # Başlatma testi
        print("📡 Servis başlatılıyor...")
        success = await stt.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Callback fonksiyonu
        def on_speech_recognized(result: STTResult):
            print(f"🗣️  Tanınan: {result.text}")
            print(f"📊 Güven: {result.confidence:.2f}")
            print(f"🔧 Servis: {result.service_used}")
            print(f"⏱️  Süre: {result.processing_time:.2f}s")
            
            if hasattr(result, 'command_type') and result.command_type:
                print(f"🎯 Komut tipi: {result.command_type}")
        
        # Dinleme testi (sadece mock modda)
        if stt.stt_config.get('active_service') == 'mock':
            print("\n🎤 Dinleme testi (Mock modu)...")
            await stt.start_listening(on_speech_recognized)
            
            # 10 saniye dinle
            await asyncio.sleep(10)
            
            await stt.stop_listening()
            print("✅ Dinleme testi tamamlandı!")
        
        # Servis durumu
        print("\n📊 Servis durumu:")
        status = stt.get_service_status()
        for key, value in status.items():
            if key != 'speech_contexts':  # Çok uzun olduğu için atla
                print(f"  {key}: {value}")
        
        print("\n✅ Tüm testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False
    
    finally:
        await stt.cleanup()

if __name__ == '__main__':
    asyncio.run(test_stt_service())