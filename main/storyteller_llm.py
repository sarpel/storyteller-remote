#!/usr/bin/env python3
"""
StorytellerLLM Service - Türkçe Hikaye Anlatma Servisi
5 yaşındaki çocuklar için özel olarak tasarlanmış hikaye üretim sistemi
"""

import os
import sys
import json
import asyncio
import logging
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class StorytellerLLM:
    """Türkçe hikaye anlatma servisi"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self.gemini_model = None
        self.is_initialized = False
        self.story_history = []
        self.current_session = None
        
        # Çocuk konfigürasyonu
        self.child_config = {
            'name': os.getenv('CHILD_NAME', 'Küçük Prenses'),
            'age': int(os.getenv('CHILD_AGE', '5')),
            'gender': os.getenv('CHILD_GENDER', 'kız'),
            'language': 'turkish'
        }
        
        # Hikaye konfigürasyonu
        self.story_config = {
            'themes': os.getenv('STORY_THEMES', 'prenses,peri,dostluk,macera,hayvanlar').split(','),
            'length': os.getenv('STORY_LENGTH', 'short'),
            'tone': os.getenv('STORY_TONE', 'gentle_enthusiastic'),
            'include_moral': os.getenv('STORY_INCLUDE_MORAL', 'true').lower() == 'true',
            'avoid_scary': os.getenv('STORY_AVOID_SCARY', 'true').lower() == 'true',
            'content_filter': os.getenv('STORY_CONTENT_FILTER', 'very_strict')
        }
        
        # LLM konfigürasyonu
        self.llm_config = {
            'service': os.getenv('LLM_SERVICE', 'openai'),
            'model': os.getenv('LLM_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.8')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '800')),
            'top_p': float(os.getenv('LLM_TOP_P', '0.9')),
            'frequency_penalty': float(os.getenv('LLM_FREQUENCY_PENALTY', '0.1')),
            'presence_penalty': float(os.getenv('LLM_PRESENCE_PENALTY', '0.1'))
        }
        
        # API konfigürasyonu
        self.api_config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            'timeout': 30.0
        }
        
        # Türkçe sistem promptları
        self.system_prompts = {
            'main_system_prompt': '''Sen 5 yaşındaki sevimli bir kız çocuğu için hikaye anlatan özel asistansın. 
            Adın "Hikaye Asistanı" ve sen her zaman nazik, sevecen ve eğlenceli hikayeleri anlatırsın.
            
            KURALLAR:
            1. Hikayelerin hep güzel, pozitif ve yaşa uygun olmalı
            2. Korkunç, üzücü veya korkutucu şeyler anlatmamalısın
            3. Her hikaye 2-3 dakika sürmeli (yaklaşık 150-200 kelime)
            4. Prenses, peri, dostluk, macera ve hayvan hikayeleri anlatmayı seviyorsun
            5. Her hikayenin sonunda güzel bir mesaj olmalı
            6. Türkçe konuşmalısın ve kelimelerini çocuğun anlayabileceği şekilde seçmelisin
            7. Cümlelerini kısa ve anlaşılır tutmalısın
            8. Hikaye bittiğinde "Ve işte hikayemiz böyle bitiyor küçük prenses!" diyerek bitirmelisin
            
            ÖRNEK KONULAR:
            - Prenses hikayeleri
            - Peri masalları  
            - Dostluk hikayeleri
            - Sevimli hayvan hikayeleri
            - Macera hikayeleri
            - Doğa hikayeleri
            
            Her zaman çocuksu bir coşku ve sevgi ile konuşmalısın!''',
            
            'greeting_prompts': [
                "Merhaba küçük prenses! Bugün sana ne hikayesi anlatayım?",
                "Selam sevgili prensesim! Hangi hikayeyi duymak istersin?",
                "Merhaba tatlım! Bugün sana çok güzel bir hikaye anlatacağım!",
                "Selam küçük prenses! Hangi konuda hikaye istiyorsun?",
                "Merhaba canım! Bugün hangi masalı dinlemek istersin?",
                "Selam prensesim! Sana özel bir hikaye hazırladım!"
            ],
            
            'story_starters': [
                "Bir zamanlar, çok uzak diyarlarda...",
                "Masallar ülkesinde, güzel bir prenses varmış...",
                "Çok güzel bir ormanda, sevimli hayvanlar yaşarmış...",
                "Büyülü bir krallıkta, iyi kalpli bir peri varmış...",
                "Uzak bir diyarda, cesur bir küçük kız varmış...",
                "Renkli çiçeklerle dolu bahçede, tatlı bir hikaye başlar..."
            ],
            
            'story_endings': [
                "Ve işte hikayemiz böyle bitiyor küçük prenses!",
                "Hikayemiz burada son buluyor. Çok güzeldi değil mi?",
                "Ve böylece mutlu mesut yaşamışlar. Hikaye böyle bitiyor prensesim!",
                "İşte bu kadar güzel hikayemiz! Yarın yeni bir hikaye anlatırım sana!",
                "Ve bu güzel hikayemiz böyle sona eriyor. Seni çok seviyorum küçük prenses!",
                "İşte hikayemiz böyle bitiyor. Rüyalarında da güzel hikayeler göreceksin!"
            ],
            
            'moral_lessons': [
                "dostluğun ne kadar önemli olduğunu",
                "paylaşmanın güzel olduğunu",
                "iyiliğin her zaman kazandığını",
                "sevginin her şeyi yendiğini",
                "cesur olmanın önemini",
                "başkalarına yardım etmenin güzel olduğunu",
                "sabırlı olmanın değerini",
                "farklılıkların güzel olduğunu",
                "doğruluk söylemenin önemini"
            ],
            
            'theme_prompts': {
                'prenses': "Güzel bir prenses ve onun maceraları hakkında",
                'peri': "Büyülü periler ve onların yaptığı güzel işler hakkında",
                'dostluk': "Güzel dostluklar ve arkadaşlık hakkında",
                'macera': "Heyecan verici ama güvenli maceralar hakkında",
                'hayvanlar': "Sevimli hayvanlar ve onların hikayeleri hakkında",
                'doğa': "Güzel doğa, çiçekler ve rengarenk bahçeler hakkında"
            }
        }
        
        self.logger.info(f"StorytellerLLM başlatıldı - Çocuk: {self.child_config['name']}")
    
    async def initialize(self) -> bool:
        """Hikaye servisi başlatma"""
        try:
            self.logger.info("StorytellerLLM servisi başlatılıyor...")
            
            # Servis seçimine göre başlatma
            if self.llm_config['service'] == 'openai':
                success = await self._initialize_openai()
            elif self.llm_config['service'] == 'gemini':
                success = await self._initialize_gemini()
            else:
                # OpenAI'yi dene, başarısız olursa Gemini'ye geç
                success = await self._initialize_openai()
                if not success:
                    success = await self._initialize_gemini()
            
            if success:
                self.is_initialized = True
                self.logger.info("✅ StorytellerLLM servisi başarıyla başlatıldı!")
                self.logger.info(f"🎭 Konfigürasyon: {self.child_config['name']}, {self.child_config['age']} yaş, {self.child_config['gender']}")
                self.logger.info(f"📚 Hikaye temaları: {', '.join(self.story_config['themes'])}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"StorytellerLLM başlatma hatası: {e}")
            return False
    
    async def _initialize_openai(self) -> bool:
        """OpenAI client başlatma"""
        try:
            if not OPENAI_AVAILABLE:
                self.logger.error("OpenAI kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['openai_api_key'] or self.api_config['openai_api_key'] == 'YOUR_OPENAI_API_KEY':
                self.logger.error("OpenAI API anahtarı bulunamadı!")
                return False
            
            self.openai_client = OpenAI(api_key=self.api_config['openai_api_key'])
            
            # Bağlantı testi
            await self._test_openai_connection()
            
            self.llm_config['active_service'] = 'openai'
            self.logger.info("✅ OpenAI başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI başlatma hatası: {e}")
            return False
    
    async def _initialize_gemini(self) -> bool:
        """Gemini client başlatma"""
        try:
            if not GEMINI_AVAILABLE:
                self.logger.error("Gemini kütüphanesi yüklü değil!")
                return False
            
            if not self.api_config['gemini_api_key'] or self.api_config['gemini_api_key'] == 'YOUR_GEMINI_API_KEY':
                self.logger.error("Gemini API anahtarı bulunamadı!")
                return False
            
            genai.configure(api_key=self.api_config['gemini_api_key'])
            self.gemini_model = genai.GenerativeModel(self.llm_config['model'])
            
            # Bağlantı testi
            await self._test_gemini_connection()
            
            self.llm_config['active_service'] = 'gemini'
            self.logger.info("✅ Gemini başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Gemini başlatma hatası: {e}")
            return False
    
    async def _test_openai_connection(self) -> bool:
        """OpenAI API bağlantı testi"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=self.llm_config['model'],
                    messages=[
                        {"role": "system", "content": "Sen hikaye anlatan bir asistansın."},
                        {"role": "user", "content": "Test mesajı"}
                    ],
                    max_tokens=50,
                    temperature=0.7
                )
            )
            
            self.logger.info("✅ OpenAI API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI API bağlantı testi başarısız: {e}")
            raise
    
    async def _test_gemini_connection(self) -> bool:
        """Gemini API bağlantı testi"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.gemini_model.generate_content("Test mesajı")
            )
            
            self.logger.info("✅ Gemini API bağlantısı başarılı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Gemini API bağlantı testi başarısız: {e}")
            raise
    
    def get_random_greeting(self) -> str:
        """Rastgele karşılama mesajı"""
        return random.choice(self.system_prompts['greeting_prompts'])
    
    def get_random_story_starter(self) -> str:
        """Rastgele hikaye başlangıcı"""
        return random.choice(self.system_prompts['story_starters'])
    
    def get_random_story_ending(self) -> str:
        """Rastgele hikaye sonu"""
        return random.choice(self.system_prompts['story_endings'])
    
    def get_random_moral_lesson(self) -> str:
        """Rastgele ahlaki ders"""
        return random.choice(self.system_prompts['moral_lessons'])
    
    def create_story_prompt(self, topic: Optional[str] = None, theme: Optional[str] = None) -> str:
        """Hikaye promptu oluşturma"""
        starter = self.get_random_story_starter()
        ending = self.get_random_story_ending()
        moral = self.get_random_moral_lesson()
        
        # Tema seçimi
        if not theme:
            theme = random.choice(self.story_config['themes'])
        
        theme_prompt = self.system_prompts['theme_prompts'].get(theme, "güzel bir konu hakkında")
        
        prompt = f"""
        GÖREV: {self.child_config['name']} isimli {self.child_config['age']} yaşındaki küçük prenses için bir hikaye anlat.
        
        Hikaye şöyle başlasın: "{starter}"
        
        Konu: {theme_prompt}
        {f"Özel istek: {topic}" if topic else ""}
        
        Hikayenin sonunda {moral} öğretmelisin.
        
        Hikayen tam olarak 150-200 kelime olmalı ve "{ending}" şeklinde bitmelisin.
        
        ÖNEMLİ KURALLAR:
        - Sadece Türkçe konuş
        - 5 yaşına uygun kelimeler kullan
        - Kısa ve anlaşılır cümleler kur
        - Korkunç, üzücü şeyler anlatma
        - Hikayeyi eğlenceli ve sevecen anlat
        - Güzel bir mesaj ver
        """
        
        return prompt
    
    async def generate_story(self, topic: Optional[str] = None, theme: Optional[str] = None) -> Dict[str, Any]:
        """Hikaye üretme"""
        if not self.is_initialized:
            raise RuntimeError("StorytellerLLM servisi başlatılmamış!")
        
        try:
            self.logger.info(f"Hikaye üretiliyor... Konu: {topic}, Tema: {theme}")
            
            # Hikaye promptu oluştur
            story_prompt = self.create_story_prompt(topic, theme)
            
            # Aktif servisi kullanarak hikaye üret
            if self.llm_config['active_service'] == 'openai':
                story_text = await self._generate_with_openai(story_prompt)
            else:
                story_text = await self._generate_with_gemini(story_prompt)
            
            # Hikaye verilerini oluştur
            story_data = {
                'text': story_text,
                'topic': topic,
                'theme': theme or random.choice(self.story_config['themes']),
                'child_name': self.child_config['name'],
                'timestamp': datetime.now().isoformat(),
                'language': 'turkish',
                'target_audience': f"{self.child_config['age']}_year_old_{self.child_config['gender']}",
                'word_count': len(story_text.split()),
                'estimated_duration': len(story_text.split()) * 0.6,  # Türkçe için
                'model_used': self.llm_config['model'],
                'service_used': self.llm_config['active_service'],
                'content_filter_level': self.story_config['content_filter']
            }
            
            # Geçmişe ekle
            self.story_history.append(story_data)
            
            # Son 10 hikayeyi tut
            if len(self.story_history) > 10:
                self.story_history = self.story_history[-10:]
            
            self.logger.info(f"✅ Hikaye başarıyla üretildi! Kelime sayısı: {story_data['word_count']}")
            self.logger.info(f"📖 Tahmini süre: {story_data['estimated_duration']:.1f} saniye")
            
            return story_data
            
        except Exception as e:
            self.logger.error(f"Hikaye üretme hatası: {e}")
            raise
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """OpenAI ile hikaye üretme"""
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.openai_client.chat.completions.create(
                model=self.llm_config['model'],
                messages=[
                    {"role": "system", "content": self.system_prompts['main_system_prompt']},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.llm_config['max_tokens'],
                temperature=self.llm_config['temperature'],
                top_p=self.llm_config['top_p'],
                frequency_penalty=self.llm_config['frequency_penalty'],
                presence_penalty=self.llm_config['presence_penalty']
            )
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Gemini ile hikaye üretme"""
        full_prompt = f"{self.system_prompts['main_system_prompt']}\n\n{prompt}"
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.gemini_model.generate_content(full_prompt)
        )
        
        return response.text.strip()
    
    async def generate_greeting(self) -> str:
        """Kişiselleştirilmiş karşılama üretme"""
        try:
            greeting_prompt = f"""
            {self.child_config['name']} isimli {self.child_config['age']} yaşındaki küçük prenses için 
            sıcak ve sevecen bir karşılama sözü söyle. Ona hikaye anlatacağını ve ne tür hikaye 
            istediğini sor. Çok kısa (1-2 cümle) olsun.
            """
            
            if not self.is_initialized:
                return self.get_random_greeting()
            
            if self.llm_config['active_service'] == 'openai':
                greeting = await self._generate_with_openai(greeting_prompt)
            else:
                greeting = await self._generate_with_gemini(greeting_prompt)
            
            self.logger.info(f"Kişiselleştirilmiş karşılama üretildi: {greeting[:50]}...")
            
            return greeting
            
        except Exception as e:
            self.logger.error(f"Karşılama üretme hatası: {e}")
            return self.get_random_greeting()
    
    async def continue_story(self, story_context: str, user_input: str) -> str:
        """Mevcut hikayeyi devam ettirme"""
        try:
            continue_prompt = f"""
            Bu hikayenin devamını getir:
            
            Önceki hikaye: {story_context}
            
            Çocuğun isteği: {user_input}
            
            Hikayeyi 2-3 cümle ile devam ettir. Hikayeyi güzel bir şekilde bitir.
            """
            
            if not self.is_initialized:
                return "Hikaye devam ettirilemiyor. Servis hazır değil."
            
            if self.llm_config['active_service'] == 'openai':
                continuation = await self._generate_with_openai(continue_prompt)
            else:
                continuation = await self._generate_with_gemini(continue_prompt)
            
            self.logger.info("Hikaye devamı üretildi")
            
            return continuation
            
        except Exception as e:
            self.logger.error(f"Hikaye devamı hatası: {e}")
            return "Üzgünüm, hikayeyi devam ettiremiyorum. Yeni bir hikaye anlatayım mı?"
    
    def get_story_history(self) -> List[Dict[str, Any]]:
        """Hikaye geçmişini getir"""
        return self.story_history.copy()
    
    def get_last_story(self) -> Optional[Dict[str, Any]]:
        """Son hikayeyi getir"""
        return self.story_history[-1] if self.story_history else None
    
    def get_available_themes(self) -> List[str]:
        """Mevcut temaları getir"""
        return self.story_config['themes'].copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Servis durumunu getir"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'StorytellerLLM',
            'language': 'turkish',
            'child_config': self.child_config,
            'story_config': self.story_config,
            'stories_generated': len(self.story_history),
            'last_story_time': self.story_history[-1]['timestamp'] if self.story_history else None,
            'available_themes': self.get_available_themes(),
            'active_service': self.llm_config.get('active_service', 'none'),
            'api_model': self.llm_config['model'],
            'processing_mode': 'remote_only',
            'openai_available': OPENAI_AVAILABLE,
            'gemini_available': GEMINI_AVAILABLE
        }
    
    async def cleanup(self) -> None:
        """Kaynakları temizle"""
        try:
            if self.openai_client:
                pass  # OpenAI client explicit cleanup gerektirmez
            
            if self.gemini_model:
                pass  # Gemini explicit cleanup gerektirmez
            
            self.is_initialized = False
            self.logger.info("StorytellerLLM servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")

# Test fonksiyonu
async def test_storyteller():
    """Hikaye servisi testi"""
    print("🎭 StorytellerLLM Test Başlıyor...")
    
    # Servisi başlat
    storyteller = StorytellerLLM()
    
    try:
        # Başlatma testi
        print("📚 Servis başlatılıyor...")
        success = await storyteller.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Karşılama testi
        print("\n👋 Karşılama testi...")
        greeting = await storyteller.generate_greeting()
        print(f"Karşılama: {greeting}")
        
        # Hikaye üretim testi
        print("\n📖 Hikaye üretim testi...")
        story = await storyteller.generate_story(theme='prenses')
        print(f"Hikaye: {story['text'][:100]}...")
        print(f"Kelime sayısı: {story['word_count']}")
        print(f"Tahmini süre: {story['estimated_duration']:.1f} saniye")
        
        # Servis durumu
        print("\n📊 Servis durumu:")
        status = storyteller.get_service_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Tüm testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False
    
    finally:
        await storyteller.cleanup()

if __name__ == '__main__':
    asyncio.run(test_storyteller())