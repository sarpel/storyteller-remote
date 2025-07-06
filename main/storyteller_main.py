#!/usr/bin/env python3
"""
StorytellerPi Ana Uygulama - Türkçe Hikaye Anlatma Sistemi
5 yaşındaki çocuklar için özel olarak tasarlanmış interaktif hikaye anlatma uygulaması
"""

import os
import sys
import asyncio
import logging
import json
import signal
import time
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Local imports
from storyteller_llm import StorytellerLLM
from stt_service import STTService, STTResult
from tts_service import TTSService
from wake_word_detector import WakeWordDetector
from audio_feedback import AudioFeedback

@dataclass
class StorySession:
    """Hikaye oturumu"""
    session_id: str
    child_name: str
    start_time: datetime
    current_story: Optional[str] = None
    story_count: int = 0
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    session_duration: float = 0.0
    is_active: bool = True

class StorytellerMain:
    """Ana hikaye anlatma uygulaması"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.current_session = None
        self.session_history = []
        
        # Temel konfigürasyon
        self.config = {
            'child_name': os.getenv('CHILD_NAME', 'Küçük Prenses'),
            'child_age': int(os.getenv('CHILD_AGE', '5')),
            'child_gender': os.getenv('CHILD_GENDER', 'kız'),
            'language': 'turkish',
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', '1800')),  # 30 dakika
            'max_stories_per_session': int(os.getenv('MAX_STORIES_PER_SESSION', '5')),
            'auto_save_sessions': os.getenv('AUTO_SAVE_SESSIONS', 'true').lower() == 'true',
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        }
        
        # Hikaye akış konfigürasyonu
        self.story_flow = {
            'greeting_enabled': True,
            'wake_word_enabled': True,
            'voice_interaction_enabled': True,
            'story_continuation_enabled': True,
            'goodbye_enabled': True,
            'feedback_enabled': True,
            'session_management_enabled': True
        }
        
        # Servis durumları
        self.services = {
            'storyteller_llm': None,
            'stt_service': None,
            'tts_service': None,
            'wake_word_detector': None,
            'audio_feedback': None
        }
        
        # Uygulama durumu
        self.app_state = {
            'current_mode': 'idle',  # idle, listening, processing, speaking, story_telling
            'last_wake_word': None,
            'last_user_input': None,
            'last_story_generated': None,
            'error_count': 0,
            'startup_time': datetime.now(),
            'total_sessions': 0,
            'total_stories': 0
        }
        
        # Türkçe mesajlar
        self.messages = {
            'greeting': [
                f"Merhaba {self.config['child_name']}! Bugün sana ne hikayesi anlatayım?",
                f"Selam sevgili {self.config['child_name']}! Hangi hikayeyi duymak istersin?",
                f"Merhaba canım {self.config['child_name']}! Bugün sana çok güzel bir hikaye anlatacağım!"
            ],
            'wake_word_detected': [
                "Evet, dinliyorum seni!",
                "Söyle bakalım, ne istiyorsun?",
                "Buradayım, ne hikayesi dinlemek istersin?"
            ],
            'story_request_received': [
                "Harika bir seçim! Hemen hikayeni hazırlıyorum...",
                "Çok güzel! Bu hikayeyi çok seveceksin...",
                "Mükemmel! Sana özel bir hikaye anlatacağım..."
            ],
            'story_finished': [
                "Ve işte hikayemiz böyle bitiyor! Beğendin mi?",
                "Hikayemiz burada son buluyor. Nasıldı?",
                "İşte bu kadar güzel hikayemiz! Başka hikaye ister misin?"
            ],
            'goodbye': [
                f"Güle güle {self.config['child_name']}! Yarın yeni hikayeler anlatırım!",
                f"Hoşça kal sevgili {self.config['child_name']}! Rüyalarında güzel hikayeler gör!",
                f"İyi geceler {self.config['child_name']}! Seni çok seviyorum!"
            ],
            'error': [
                "Üzgünüm, bir sorun oldu. Tekrar dener misin?",
                "Anlayamadım, tekrar söyler misin?",
                "Bir dakika bekle, hemen düzeltiyorum..."
            ],
            'session_timeout': [
                "Uzun süredir konuşmuyoruz. Başka zaman hikaye anlatırım!",
                "Sanırım yoruldun. İstersen sonra devam ederiz!",
                "Biraz dinlen, sonra yeni hikayeler anlatırım!"
            ]
        }
        
        self.logger.info(f"StorytellerMain başlatıldı - {self.config['child_name']} için hazır")
    
    async def initialize(self) -> bool:
        """Uygulamayı başlat"""
        try:
            self.logger.info("🎭 StorytellerPi başlatılıyor...")
            
            # Servisleri başlat
            success = await self._initialize_services()
            
            if not success:
                self.logger.error("Servisler başlatılamadı!")
                return False
            
            # Signal handler'ları ayarla
            self._setup_signal_handlers()
            
            # İlk oturum hazırlığı
            await self._prepare_first_session()
            
            self.logger.info("✅ StorytellerPi başarıyla başlatıldı!")
            self.logger.info(f"👶 Çocuk: {self.config['child_name']}, {self.config['child_age']} yaş")
            self.logger.info(f"🎯 Mod: {self.app_state['current_mode']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Başlatma hatası: {e}")
            return False
    
    async def _initialize_services(self) -> bool:
        """Tüm servisleri başlat"""
        try:
            # StorytellerLLM servisini başlat
            self.logger.info("📚 StorytellerLLM başlatılıyor...")
            self.services['storyteller_llm'] = StorytellerLLM()
            
            llm_success = await self.services['storyteller_llm'].initialize()
            if not llm_success:
                self.logger.warning("StorytellerLLM başlatılamadı - mock moda geçiliyor")
            
            # TTS servisini başlat
            self.logger.info("🔊 TTS servisi başlatılıyor...")
            self.services['tts_service'] = TTSService()
            
            tts_success = await self.services['tts_service'].initialize()
            if not tts_success:
                self.logger.warning("TTS servisi başlatılamadı - mock moda geçiliyor")
            
            # STT servisini başlat
            self.logger.info("🎤 STT servisi başlatılıyor...")
            self.services['stt_service'] = STTService()
            
            stt_success = await self.services['stt_service'].initialize()
            if not stt_success:
                self.logger.warning("STT servisi başlatılamadı - mock moda geçiliyor")
            
            # Wake Word Detector'ı başlat
            self.logger.info("👂 Wake Word Detector başlatılıyor...")
            self.services['wake_word_detector'] = WakeWordDetector()
            
            wake_success = await self.services['wake_word_detector'].initialize()
            if not wake_success:
                self.logger.warning("Wake Word Detector başlatılamadı - devre dışı")
                self.story_flow['wake_word_enabled'] = False
            
            # Audio Feedback'i başlat
            self.logger.info("🎵 Audio Feedback başlatılıyor...")
            self.services['audio_feedback'] = AudioFeedback()
            
            audio_success = await self.services['audio_feedback'].initialize()
            if not audio_success:
                self.logger.warning("Audio Feedback başlatılamadı - devre dışı")
                self.story_flow['feedback_enabled'] = False
            
            # En az temel servisler çalışıyor mu kontrol et
            if not (llm_success or tts_success):
                self.logger.error("Kritik servisler başlatılamadı!")
                return False
            
            self.logger.info("✅ Tüm servisler başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Servis başlatma hatası: {e}")
            return False
    
    def _setup_signal_handlers(self) -> None:
        """Signal handler'ları ayarla"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            self.logger.info("Signal handler'lar ayarlandı")
        except Exception as e:
            self.logger.error(f"Signal handler ayarlama hatası: {e}")
    
    def _signal_handler(self, signum, frame):
        """Signal handler"""
        self.logger.info(f"Signal alındı: {signum}")
        asyncio.create_task(self.shutdown())
    
    async def _prepare_first_session(self) -> None:
        """İlk oturum hazırlığı"""
        try:
            # Yeni oturum başlat
            await self._start_new_session()
            
            # Karşılama mesajı hazırla
            if self.services['storyteller_llm'] and self.services['storyteller_llm'].is_initialized:
                greeting = await self.services['storyteller_llm'].generate_greeting()
            else:
                import random
                greeting = random.choice(self.messages['greeting'])
            
            # Karşılama mesajını seslendir
            if self.services['tts_service'] and self.services['tts_service'].is_initialized:
                await self.services['tts_service'].speak_text(greeting)
            
            # Dinleme moduna geç
            await self._set_mode('listening')
            
            self.logger.info("İlk oturum hazırlandı")
            
        except Exception as e:
            self.logger.error(f"İlk oturum hazırlama hatası: {e}")
    
    async def _start_new_session(self) -> None:
        """Yeni oturum başlat"""
        try:
            session_id = f"session_{int(time.time())}"
            
            self.current_session = StorySession(
                session_id=session_id,
                child_name=self.config['child_name'],
                start_time=datetime.now()
            )
            
            self.app_state['total_sessions'] += 1
            
            self.logger.info(f"🎯 Yeni oturum başlatıldı: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Yeni oturum başlatma hatası: {e}")
    
    async def _set_mode(self, mode: str) -> None:
        """Uygulama modunu değiştir"""
        try:
            old_mode = self.app_state['current_mode']
            self.app_state['current_mode'] = mode
            
            self.logger.info(f"🔄 Mod değişti: {old_mode} → {mode}")
            
            # Moda göre işlemler
            if mode == 'listening':
                await self._start_listening()
            elif mode == 'idle':
                await self._stop_listening()
            elif mode == 'processing':
                await self._stop_listening()
            
        except Exception as e:
            self.logger.error(f"Mod değiştirme hatası: {e}")
    
    async def _start_listening(self) -> None:
        """Dinlemeyi başlat"""
        try:
            # Wake word detector'ı başlat
            if self.story_flow['wake_word_enabled'] and self.services['wake_word_detector']:
                await self.services['wake_word_detector'].start_detection(self._on_wake_word_detected)
            
            # STT servisini başlat
            if self.story_flow['voice_interaction_enabled'] and self.services['stt_service']:
                await self.services['stt_service'].start_listening(self._on_speech_recognized)
            
            self.logger.info("🎤 Dinleme başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Dinleme başlatma hatası: {e}")
    
    async def _stop_listening(self) -> None:
        """Dinlemeyi durdur"""
        try:
            # Wake word detector'ı durdur
            if self.services['wake_word_detector']:
                await self.services['wake_word_detector'].stop_detection()
            
            # STT servisini durdur
            if self.services['stt_service']:
                await self.services['stt_service'].stop_listening()
            
            self.logger.info("🔇 Dinleme durduruldu")
            
        except Exception as e:
            self.logger.error(f"Dinleme durdurma hatası: {e}")
    
    async def _on_wake_word_detected(self, wake_word: str) -> None:
        """Wake word algılandığında çağrılır"""
        try:
            self.logger.info(f"👂 Wake word algılandı: {wake_word}")
            
            self.app_state['last_wake_word'] = wake_word
            
            # Ses geri bildirimi
            if self.story_flow['feedback_enabled'] and self.services['audio_feedback']:
                await self.services['audio_feedback'].play_wake_sound()
            
            # Yanıt mesajı
            import random
            response = random.choice(self.messages['wake_word_detected'])
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(response)
            
            # Dinleme moduna geç
            await self._set_mode('listening')
            
        except Exception as e:
            self.logger.error(f"Wake word işleme hatası: {e}")
    
    async def _on_speech_recognized(self, result: STTResult) -> None:
        """Konuşma tanındığında çağrılır"""
        try:
            self.logger.info(f"🗣️  Konuşma tanındı: {result.text}")
            
            self.app_state['last_user_input'] = result.text
            
            # Oturum güncellemesi
            if self.current_session:
                self.current_session.interaction_count += 1
                self.current_session.last_interaction = datetime.now()
            
            # İşleme moduna geç
            await self._set_mode('processing')
            
            # Kullanıcı isteğini işle
            await self._process_user_request(result.text)
            
        except Exception as e:
            self.logger.error(f"Konuşma işleme hatası: {e}")
    
    async def _process_user_request(self, user_input: str) -> None:
        """Kullanıcı isteğini işle"""
        try:
            user_input_lower = user_input.lower()
            
            # Dur/çıkış komutları
            if any(word in user_input_lower for word in ['dur', 'bitir', 'çık', 'yeter', 'vazgeç']):
                await self._handle_stop_request()
                return
            
            # Hikaye istekleri
            if any(word in user_input_lower for word in ['hikaye', 'masal', 'anlat', 'söyle', 'istiyorum']):
                await self._handle_story_request(user_input)
                return
            
            # Genel sohbet
            await self._handle_general_chat(user_input)
            
        except Exception as e:
            self.logger.error(f"Kullanıcı isteği işleme hatası: {e}")
            await self._handle_error()
    
    async def _handle_story_request(self, user_input: str) -> None:
        """Hikaye isteğini işle"""
        try:
            self.logger.info(f"📖 Hikaye isteği işleniyor: {user_input}")
            
            # Hikaye onay mesajı
            import random
            confirmation = random.choice(self.messages['story_request_received'])
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(confirmation)
            
            # Hikaye anlatım moduna geç
            await self._set_mode('story_telling')
            
            # Hikaye üret
            if self.services['storyteller_llm'] and self.services['storyteller_llm'].is_initialized:
                story_data = await self.services['storyteller_llm'].generate_story(topic=user_input)
                
                if story_data:
                    # Hikayeyi seslendir
                    if self.services['tts_service']:
                        await self.services['tts_service'].speak_text(story_data['text'])
                    
                    # Oturum güncellemesi
                    if self.current_session:
                        self.current_session.story_count += 1
                        self.current_session.current_story = story_data['text']
                    
                    self.app_state['last_story_generated'] = story_data
                    self.app_state['total_stories'] += 1
                    
                    self.logger.info(f"✅ Hikaye başarıyla anlatıldı!")
                    
                    # Hikaye bitişi mesajı
                    ending_message = random.choice(self.messages['story_finished'])
                    
                    if self.services['tts_service']:
                        await self.services['tts_service'].speak_text(ending_message)
                    
                else:
                    await self._handle_error()
            else:
                # Mock hikaye
                mock_story = f"""
                Bir zamanlar, {self.config['child_name']} adında çok güzel bir prenses varmış. 
                Bu prenses çok akıllı ve cesurmuş. Bir gün ormanda yürürken, 
                sevimli bir tavşanla karşılaşmış. Tavşan ona çok güzel bir bahçe göstermiş. 
                Bahçede renkli çiçekler ve güzel kokular varmış. 
                Prenses ve tavşan çok güzel arkadaş olmuşlar. 
                Ve işte hikayemiz böyle bitiyor küçük prenses!
                """
                
                if self.services['tts_service']:
                    await self.services['tts_service'].speak_text(mock_story)
            
            # Dinleme moduna geri dön
            await self._set_mode('listening')
            
        except Exception as e:
            self.logger.error(f"Hikaye isteği işleme hatası: {e}")
            await self._handle_error()
    
    async def _handle_general_chat(self, user_input: str) -> None:
        """Genel sohbet işle"""
        try:
            self.logger.info(f"💬 Genel sohbet: {user_input}")
            
            # Basit yanıtlar
            responses = {
                'merhaba': f"Merhaba {self.config['child_name']}! Nasılsın?",
                'nasılsın': "Ben çok iyiyim! Sen nasılsın?",
                'teşekkür': "Rica ederim canım! Başka bir şey ister misin?",
                'güzel': "Çok sevindim! Başka hikaye ister misin?",
                'evet': "Harika! Ne yapmak istersin?",
                'hayır': "Tamam canım, başka zaman!",
                'seviyorum': f"Ben de seni çok seviyorum {self.config['child_name']}!",
                'güle güle': f"Güle güle {self.config['child_name']}! Görüşürüz!"
            }
            
            user_input_lower = user_input.lower()
            response = None
            
            for key, value in responses.items():
                if key in user_input_lower:
                    response = value
                    break
            
            if not response:
                response = f"Anlıyorum {self.config['child_name']}. Hikaye anlatmak ister misin?"
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(response)
            
            # Dinleme moduna geri dön
            await self._set_mode('listening')
            
        except Exception as e:
            self.logger.error(f"Genel sohbet hatası: {e}")
            await self._handle_error()
    
    async def _handle_stop_request(self) -> None:
        """Dur/çıkış isteğini işle"""
        try:
            self.logger.info("🛑 Dur/çıkış isteği alındı")
            
            # Veda mesajı
            import random
            goodbye = random.choice(self.messages['goodbye'])
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(goodbye)
            
            # Oturumu sonlandır
            await self._end_current_session()
            
            # Uygulamayı kapat
            await self.shutdown()
            
        except Exception as e:
            self.logger.error(f"Dur isteği işleme hatası: {e}")
    
    async def _handle_error(self) -> None:
        """Hata durumunu işle"""
        try:
            self.app_state['error_count'] += 1
            
            # Hata mesajı
            import random
            error_message = random.choice(self.messages['error'])
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(error_message)
            
            # Dinleme moduna geri dön
            await self._set_mode('listening')
            
        except Exception as e:
            self.logger.error(f"Hata işleme hatası: {e}")
    
    async def _end_current_session(self) -> None:
        """Mevcut oturumu sonlandır"""
        try:
            if self.current_session:
                self.current_session.is_active = False
                self.current_session.session_duration = (
                    datetime.now() - self.current_session.start_time
                ).total_seconds()
                
                # Oturumu geçmişe ekle
                self.session_history.append(self.current_session)
                
                # Oturum kaydet
                if self.config['auto_save_sessions']:
                    await self._save_session(self.current_session)
                
                self.logger.info(f"📊 Oturum sonlandırıldı: {self.current_session.session_id}")
                self.logger.info(f"   Süre: {self.current_session.session_duration:.1f}s")
                self.logger.info(f"   Hikaye sayısı: {self.current_session.story_count}")
                self.logger.info(f"   Etkileşim sayısı: {self.current_session.interaction_count}")
                
                self.current_session = None
            
        except Exception as e:
            self.logger.error(f"Oturum sonlandırma hatası: {e}")
    
    async def _save_session(self, session: StorySession) -> None:
        """Oturumu kaydet"""
        try:
            sessions_dir = Path('sessions')
            sessions_dir.mkdir(exist_ok=True)
            
            session_file = sessions_dir / f"{session.session_id}.json"
            
            session_data = asdict(session)
            session_data['start_time'] = session.start_time.isoformat()
            if session.last_interaction:
                session_data['last_interaction'] = session.last_interaction.isoformat()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Oturum kaydedildi: {session_file}")
            
        except Exception as e:
            self.logger.error(f"Oturum kaydetme hatası: {e}")
    
    async def run(self) -> None:
        """Ana döngüyü çalıştır"""
        try:
            self.is_running = True
            self.logger.info("🚀 StorytellerPi çalışıyor...")
            
            # Ana döngü
            while self.is_running:
                try:
                    # Oturum zaman aşımı kontrolü
                    if self.current_session and self.current_session.last_interaction:
                        time_since_last = (datetime.now() - self.current_session.last_interaction).total_seconds()
                        
                        if time_since_last > self.config['session_timeout']:
                            await self._handle_session_timeout()
                    
                    # Kısa bekleme
                    await asyncio.sleep(1)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt alındı")
                    break
                except Exception as e:
                    self.logger.error(f"Ana döngü hatası: {e}")
                    await asyncio.sleep(5)
            
        except Exception as e:
            self.logger.error(f"Ana döngü kritik hatası: {e}")
        finally:
            await self.shutdown()
    
    async def _handle_session_timeout(self) -> None:
        """Oturum zaman aşımını işle"""
        try:
            self.logger.info("⏰ Oturum zaman aşımı")
            
            # Zaman aşımı mesajı
            import random
            timeout_message = random.choice(self.messages['session_timeout'])
            
            if self.services['tts_service']:
                await self.services['tts_service'].speak_text(timeout_message)
            
            # Oturumu sonlandır
            await self._end_current_session()
            
            # Yeni oturum hazırla
            await self._prepare_first_session()
            
        except Exception as e:
            self.logger.error(f"Oturum zaman aşımı işleme hatası: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Uygulama durumunu getir"""
        try:
            status = {
                'app_info': {
                    'name': 'StorytellerPi',
                    'version': '1.0.0',
                    'language': 'turkish',
                    'child_name': self.config['child_name'],
                    'child_age': self.config['child_age'],
                    'is_running': self.is_running,
                    'current_mode': self.app_state['current_mode'],
                    'startup_time': self.app_state['startup_time'].isoformat(),
                    'total_sessions': self.app_state['total_sessions'],
                    'total_stories': self.app_state['total_stories'],
                    'error_count': self.app_state['error_count']
                },
                'current_session': None,
                'services': {},
                'story_flow': self.story_flow
            }
            
            # Mevcut oturum bilgisi
            if self.current_session:
                status['current_session'] = {
                    'session_id': self.current_session.session_id,
                    'start_time': self.current_session.start_time.isoformat(),
                    'story_count': self.current_session.story_count,
                    'interaction_count': self.current_session.interaction_count,
                    'is_active': self.current_session.is_active
                }
            
            # Servis durumları
            for service_name, service in self.services.items():
                if service:
                    try:
                        status['services'][service_name] = service.get_service_status()
                    except:
                        status['services'][service_name] = {'initialized': False, 'error': True}
                else:
                    status['services'][service_name] = {'initialized': False, 'not_loaded': True}
            
            return status
            
        except Exception as e:
            self.logger.error(f"Durum getirme hatası: {e}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Uygulamayı kapat"""
        try:
            self.logger.info("🔄 StorytellerPi kapatılıyor...")
            
            self.is_running = False
            
            # Mevcut oturumu sonlandır
            if self.current_session:
                await self._end_current_session()
            
            # Servisleri temizle
            for service_name, service in self.services.items():
                if service:
                    try:
                        await service.cleanup()
                        self.logger.info(f"✅ {service_name} temizlendi")
                    except Exception as e:
                        self.logger.error(f"❌ {service_name} temizleme hatası: {e}")
            
            self.logger.info("👋 StorytellerPi kapatıldı!")
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")

# Ana fonksiyon
async def main():
    """Ana fonksiyon"""
    # Logging ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('storyteller.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🎭 StorytellerPi Başlatılıyor...")
    
    # Uygulamayı başlat
    app = StorytellerMain()
    
    try:
        # Başlatma
        success = await app.initialize()
        
        if not success:
            logger.error("❌ Uygulama başlatılamadı!")
            return
        
        # Ana döngüyü çalıştır
        await app.run()
        
    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Kritik hata: {e}")
    finally:
        await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())