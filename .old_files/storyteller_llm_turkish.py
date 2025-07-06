#!/usr/bin/env python3
"""
Turkish StorytellerLLM Service
Optimized for 5-year-old girl with remote OpenAI GPT-4 processing
No local models - everything via API
"""

import os
import sys
import json
import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

class TurkishStorytellerLLM:
    """Turkish storyteller LLM service optimized for 5-year-old girl"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.is_initialized = False
        self.story_history = []
        self.current_session = None
        
        # Turkish storytelling configuration
        self.child_config = {
            'name': os.getenv('CHILD_NAME', 'Küçük Prenses'),
            'age': int(os.getenv('CHILD_AGE', '5')),
            'gender': os.getenv('CHILD_GENDER', 'kız'),
            'language': os.getenv('STORY_LANGUAGE', 'turkish'),
            'target_audience': os.getenv('STORY_TARGET_AUDIENCE', '5_year_old_girl')
        }
        
        # Story configuration
        self.story_config = {
            'themes': os.getenv('STORY_THEMES', 'prenses,peri,dostluk,macera,hayvanlar').split(','),
            'length': os.getenv('STORY_LENGTH', 'short'),
            'tone': os.getenv('STORY_TONE', 'gentle_enthusiastic'),
            'include_moral': os.getenv('STORY_INCLUDE_MORAL', 'true').lower() == 'true',
            'avoid_scary': os.getenv('STORY_AVOID_SCARY', 'true').lower() == 'true',
            'content_filter': os.getenv('STORY_CONTENT_FILTER', 'very_strict')
        }
        
        # OpenAI configuration
        self.openai_config = {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('LLM_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.8')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '800')),
            'top_p': float(os.getenv('LLM_TOP_P', '0.9')),
            'frequency_penalty': float(os.getenv('LLM_FREQUENCY_PENALTY', '0.1')),
            'presence_penalty': float(os.getenv('LLM_PRESENCE_PENALTY', '0.1'))
        }
        
        # Turkish system prompts
        self.system_prompts = self._load_turkish_prompts()
        
        self.logger.info(f"Turkish StorytellerLLM initialized for {self.child_config['name']}")
    
    def _load_turkish_prompts(self) -> Dict[str, Any]:
        """Load Turkish storytelling prompts"""
        return {
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
    
    async def initialize(self) -> bool:
        """Initialize the Turkish storyteller LLM service"""
        try:
            self.logger.info("Turkish StorytellerLLM servisi başlatılıyor...")
            
            # Check if OpenAI is available
            if not openai or not OpenAI:
                self.logger.error("OpenAI kütüphanesi yüklü değil!")
                return False
            
            # Check API key
            if not self.openai_config['api_key'] or self.openai_config['api_key'] == 'YOUR_OPENAI_API_KEY':
                self.logger.error("OpenAI API anahtarı bulunamadı!")
                self.logger.error("Lütfen .env dosyasında OPENAI_API_KEY değerini ayarlayın")
                return False
            
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.openai_config['api_key'])
            
            # Test connection
            await self._test_connection()
            
            self.is_initialized = True
            self.logger.info("✅ Turkish StorytellerLLM servisi başarıyla başlatıldı!")
            self.logger.info(f"🎭 Konfigürasyon: {self.child_config['name']}, {self.child_config['age']} yaş, {self.child_config['gender']}")
            self.logger.info(f"📚 Hikaye temaları: {', '.join(self.story_config['themes'])}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Turkish StorytellerLLM başlatma hatası: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            # Simple test completion
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.openai_config['model'],
                    messages=[
                        {"role": "system", "content": "Sen Türkçe hikaye anlatan bir asistansın."},
                        {"role": "user", "content": "Merhaba, test mesajı"}
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
    
    def get_random_greeting(self) -> str:
        """Get a random Turkish greeting"""
        return random.choice(self.system_prompts['greeting_prompts'])
    
    def get_random_story_starter(self) -> str:
        """Get a random Turkish story starter"""
        return random.choice(self.system_prompts['story_starters'])
    
    def get_random_story_ending(self) -> str:
        """Get a random Turkish story ending"""
        return random.choice(self.system_prompts['story_endings'])
    
    def get_random_moral_lesson(self) -> str:
        """Get a random moral lesson"""
        return random.choice(self.system_prompts['moral_lessons'])
    
    def create_story_prompt(self, topic: Optional[str] = None, theme: Optional[str] = None) -> str:
        """Create a story prompt based on topic and theme"""
        starter = self.get_random_story_starter()
        ending = self.get_random_story_ending()
        moral = self.get_random_moral_lesson()
        
        # Select theme
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
        """Generate a Turkish story for the child"""
        if not self.is_initialized:
            raise RuntimeError("Turkish StorytellerLLM servisi başlatılmamış!")
        
        try:
            self.logger.info(f"Hikaye üretiliyor... Konu: {topic}, Tema: {theme}")
            
            # Create story prompt
            story_prompt = self.create_story_prompt(topic, theme)
            
            # Generate story using OpenAI
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.openai_config['model'],
                    messages=[
                        {"role": "system", "content": self.system_prompts['main_system_prompt']},
                        {"role": "user", "content": story_prompt}
                    ],
                    max_tokens=self.openai_config['max_tokens'],
                    temperature=self.openai_config['temperature'],
                    top_p=self.openai_config['top_p'],
                    frequency_penalty=self.openai_config['frequency_penalty'],
                    presence_penalty=self.openai_config['presence_penalty']
                )
            )
            
            story_text = response.choices[0].message.content.strip()
            
            # Create story metadata
            story_data = {
                'text': story_text,
                'topic': topic,
                'theme': theme or random.choice(self.story_config['themes']),
                'child_name': self.child_config['name'],
                'timestamp': datetime.now().isoformat(),
                'language': 'turkish',
                'target_audience': self.child_config['target_audience'],
                'word_count': len(story_text.split()),
                'estimated_duration': len(story_text.split()) * 0.6,  # ~0.6 seconds per word in Turkish
                'model_used': self.openai_config['model'],
                'content_filter_level': self.story_config['content_filter']
            }
            
            # Add to history
            self.story_history.append(story_data)
            
            # Keep only last 10 stories
            if len(self.story_history) > 10:
                self.story_history = self.story_history[-10:]
            
            self.logger.info(f"✅ Hikaye başarıyla üretildi! Kelime sayısı: {story_data['word_count']}")
            self.logger.info(f"📖 Tahmini süre: {story_data['estimated_duration']:.1f} saniye")
            
            return story_data
            
        except Exception as e:
            self.logger.error(f"Hikaye üretme hatası: {e}")
            raise
    
    async def generate_greeting(self) -> str:
        """Generate a personalized Turkish greeting"""
        try:
            greeting_prompt = f"""
            {self.child_config['name']} isimli {self.child_config['age']} yaşındaki küçük prenses için 
            sıcak ve sevecen bir karşılama sözü söyle. Ona hikaye anlatacağını ve ne tür hikaye 
            istediğini sor. Çok kısa (1-2 cümle) olsun.
            """
            
            if not self.is_initialized:
                # Fallback to predefined greetings
                return self.get_random_greeting()
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.openai_config['model'],
                    messages=[
                        {"role": "system", "content": self.system_prompts['main_system_prompt']},
                        {"role": "user", "content": greeting_prompt}
                    ],
                    max_tokens=100,
                    temperature=0.8
                )
            )
            
            greeting = response.choices[0].message.content.strip()
            self.logger.info(f"Kişiselleştirilmiş karşılama üretildi: {greeting[:50]}...")
            
            return greeting
            
        except Exception as e:
            self.logger.error(f"Karşılama üretme hatası: {e}")
            # Return random greeting as fallback
            return self.get_random_greeting()
    
    async def continue_story(self, story_context: str, user_input: str) -> str:
        """Continue an existing story based on user input"""
        try:
            continue_prompt = f"""
            Bu hikayenin devamını getir:
            
            Önceki hikaye: {story_context}
            
            Çocuğun isteği: {user_input}
            
            Hikayeyi 2-3 cümle ile devam ettir. Hikayeyi güzel bir şekilde bitir.
            """
            
            if not self.is_initialized:
                return "Hikaye devam ettirilemiyor. Servis hazır değil."
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.openai_config['model'],
                    messages=[
                        {"role": "system", "content": self.system_prompts['main_system_prompt']},
                        {"role": "user", "content": continue_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.8
                )
            )
            
            continuation = response.choices[0].message.content.strip()
            self.logger.info("Hikaye devamı üretildi")
            
            return continuation
            
        except Exception as e:
            self.logger.error(f"Hikaye devamı hatası: {e}")
            return "Üzgünüm, hikayeyi devam ettiremiyorum. Yeni bir hikaye anlatayım mı?"
    
    def get_story_history(self) -> List[Dict[str, Any]]:
        """Get the story history"""
        return self.story_history.copy()
    
    def get_last_story(self) -> Optional[Dict[str, Any]]:
        """Get the last generated story"""
        return self.story_history[-1] if self.story_history else None
    
    def get_available_themes(self) -> List[str]:
        """Get available story themes"""
        return self.story_config['themes'].copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'initialized': self.is_initialized,
            'service_name': 'Turkish StorytellerLLM',
            'child_config': self.child_config,
            'story_config': self.story_config,
            'stories_generated': len(self.story_history),
            'last_story_time': self.story_history[-1]['timestamp'] if self.story_history else None,
            'available_themes': self.get_available_themes(),
            'api_model': self.openai_config['model'],
            'processing_mode': 'remote_only'
        }
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.client:
                # OpenAI client doesn't need explicit cleanup
                pass
            
            self.is_initialized = False
            self.logger.info("Turkish StorytellerLLM servisi temizlendi")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")

# Test function
async def test_turkish_storyteller():
    """Test the Turkish storyteller service"""
    print("🎭 Turkish StorytellerLLM Test Başlıyor...")
    
    # Initialize service
    storyteller = TurkishStorytellerLLM()
    
    try:
        # Test initialization
        print("📚 Servis başlatılıyor...")
        success = await storyteller.initialize()
        
        if not success:
            print("❌ Servis başlatılamadı!")
            return False
        
        print("✅ Servis başarıyla başlatıldı!")
        
        # Test greeting
        print("\n👋 Karşılama testi...")
        greeting = await storyteller.generate_greeting()
        print(f"Karşılama: {greeting}")
        
        # Test story generation
        print("\n📖 Hikaye üretim testi...")
        story = await storyteller.generate_story(theme='prenses')
        print(f"Hikaye: {story['text'][:100]}...")
        print(f"Kelime sayısı: {story['word_count']}")
        print(f"Tahmini süre: {story['estimated_duration']:.1f} saniye")
        
        # Test service status
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
    asyncio.run(test_turkish_storyteller())