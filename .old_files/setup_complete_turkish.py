#!/usr/bin/env python3
"""
Complete Turkish StorytellerPi Setup
Final integration script for Turkish language support
Optimized for 5-year-old girl with remote processing only
"""

import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

def setup_logging():
    """Setup logging for complete Turkish setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup_complete_turkish.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def install_lightweight_requirements():
    """Install lightweight requirements for remote processing"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Hafif bağımlılıklar yükleniyor...")
        
        # Use the lightweight requirements file
        requirements_file = "requirements_turkish_lightweight.txt"
        
        if not os.path.exists(requirements_file):
            logger.error(f"Gereksinimler dosyası bulunamadı: {requirements_file}")
            return False
        
        # Install requirements
        cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        
        logger.info(f"Komut çalıştırılıyor: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Hafif bağımlılıklar başarıyla yüklendi!")
            return True
        else:
            logger.error(f"❌ Bağımlılık yükleme hatası: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Bağımlılık yükleme hatası: {e}")
        return False

def create_turkish_environment():
    """Create complete Turkish environment configuration"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Türkçe ortam konfigürasyonu oluşturuluyor...")
        
        # Turkish environment configuration
        env_config = """# Turkish StorytellerPi Environment Configuration
# 5 yaşındaki küçük prenses için özel konfigürasyon
# Tüm ağır işlemler uzak API'ler ile yapılır

# ============================================================================
# TEMEL KONFIGÜRASYON
# ============================================================================

# Dil Ayarları
SYSTEM_LANGUAGE=tr-TR
SYSTEM_LOCALE=tr_TR.UTF-8
STORY_LANGUAGE=turkish
CHILD_NAME=Küçük Prenses
CHILD_AGE=5
CHILD_GENDER=kız

# ============================================================================
# UYANDIRMA KELİMESİ (YEREL - PORCUPINE)
# ============================================================================

# Porcupine Wake Word (Tek yerel işlem)
WAKE_WORD=merhaba asistan
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_SENSITIVITY=0.7
WAKE_WORD_MODEL_PATH=/opt/storytellerpi/models/merhaba-asistan.ppn
PORCUPINE_ACCESS_KEY=YOUR_PORCUPINE_ACCESS_KEY

# ============================================================================
# KONUŞMA TANIMA (UZAK - GOOGLE CLOUD)
# ============================================================================

# Google Cloud Speech-to-Text (Turkish)
STT_SERVICE=google
STT_LANGUAGE_CODE=tr-TR
STT_ALTERNATIVE_LANGUAGE=tr
STT_TIMEOUT=10.0
STT_MAX_AUDIO_LENGTH=30.0
STT_USE_LOCAL_MODELS=false
STT_REMOTE_ONLY=true
STT_SAMPLE_RATE=16000
STT_CHANNELS=1
STT_CHUNK_SIZE=1024

# Google Cloud Credentials
GOOGLE_APPLICATION_CREDENTIALS=/opt/storytellerpi/credentials/google-credentials.json

# ============================================================================
# SES SENTEZİ (UZAK - ELEVENLABS)
# ============================================================================

# ElevenLabs Text-to-Speech (Turkish)
TTS_SERVICE=elevenlabs
TTS_LANGUAGE=tr
TTS_VOICE_GENDER=female
TTS_VOICE_AGE=young_adult
TTS_VOICE_STYLE=storyteller
TTS_VOICE_STABILITY=0.8
TTS_VOICE_SIMILARITY_BOOST=0.7
TTS_MODEL_ID=eleven_turbo_v2
TTS_REMOTE_ONLY=true
TTS_USE_SPEAKER_BOOST=true
TTS_OPTIMIZE_STREAMING_LATENCY=2

# ElevenLabs API Configuration
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID=YOUR_TURKISH_VOICE_ID

# ============================================================================
# HİKAYE ÜRETİMİ (UZAK - OPENAI GPT-4)
# ============================================================================

# OpenAI GPT-4 (Turkish Stories)
LLM_SERVICE=openai
LLM_MODEL=gpt-4
LLM_LANGUAGE=turkish
LLM_TEMPERATURE=0.8
LLM_MAX_TOKENS=800
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.1
LLM_PRESENCE_PENALTY=0.1
LLM_REMOTE_ONLY=true

# OpenAI API Configuration
OPENAI_API_KEY=YOUR_OPENAI_API_KEY

# ============================================================================
# HİKAYE AYARLARI (ÇOCUK DOSTU)
# ============================================================================

# Story Configuration for 5-year-old girl
STORY_TARGET_AUDIENCE=5_year_old_girl
STORY_CONTENT_FILTER=very_strict
STORY_THEMES=prenses,peri,dostluk,macera,hayvanlar
STORY_LENGTH=short
STORY_TONE=gentle_enthusiastic
STORY_INCLUDE_MORAL=true
STORY_AVOID_SCARY=true

# Turkish Story Prompts
STORY_GREETING=Merhaba küçük prenses! Bugün sana güzel bir hikaye anlatmak istiyorum.
STORY_SYSTEM_PROMPT=Sen 5 yaşındaki küçük bir kız çocuğu için hikaye anlatan sevimli bir asistansın.

# ============================================================================
# PERFORMANS OPTİMİZASYONU (PI ZERO 2W)
# ============================================================================

# Pi Zero 2W Optimization
OPTIMIZE_FOR_PI_ZERO=true
USE_LOCAL_MODELS=false
MEMORY_LIMIT=300
CPU_LIMIT=80
DISABLE_HEAVY_PROCESSING=true
MAX_MEMORY_USAGE=300
TARGET_RESPONSE_TIME=8.0

# ============================================================================
# WEB ARAYÜZÜ (TÜRKÇE)
# ============================================================================

# Web Interface (Turkish)
WEB_ENABLED=true
WEB_LANGUAGE=tr
WEB_TITLE=Hikaye Asistanı
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false
WEB_SECRET_KEY=hikaye-asistani-secret-key

# ============================================================================
# SİSTEM AYARLARI
# ============================================================================

# System Configuration
INSTALL_DIR=/opt/storytellerpi
LOG_DIR=/opt/storytellerpi/logs
MODELS_DIR=/opt/storytellerpi/models
CREDENTIALS_DIR=/opt/storytellerpi/credentials
SERVICE_NAME=storytellerpi
LOG_LEVEL=INFO
LOG_LANGUAGE=turkish

# Audio Configuration
AUDIO_FEEDBACK_ENABLED=true
AUDIO_FEEDBACK_WAKE_WORD_TONE=880.0
AUDIO_FEEDBACK_SUCCESS_TONE=1000.0
AUDIO_FEEDBACK_ERROR_TONE=400.0

# ============================================================================
# GÜVENLİK NOTU
# ============================================================================

# ÖNEMLI: Bu dosyayı doldurmayı unutmayın!
# 1. YOUR_OPENAI_API_KEY -> OpenAI API anahtarınız
# 2. YOUR_ELEVENLABS_API_KEY -> ElevenLabs API anahtarınız  
# 3. YOUR_ELEVENLABS_VOICE_ID -> Türkçe ses ID'niz
# 4. YOUR_PORCUPINE_ACCESS_KEY -> Porcupine API anahtarınız
# 5. Google credentials JSON dosyasını yükleyin
"""
        
        # Write environment file
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_config)
        
        logger.info("✅ Türkçe ortam konfigürasyonu oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"Ortam konfigürasyonu hatası: {e}")
        return False

def setup_directory_structure():
    """Setup directory structure for Turkish StorytellerPi"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Dizin yapısı oluşturuluyor...")
        
        # Create directories
        directories = [
            'main/templates',
            'main/config',
            'main/prompts',
            'logs',
            'models',
            'credentials',
            'tests',
            'scripts'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 Dizin oluşturuldu: {directory}")
        
        logger.info("✅ Dizin yapısı tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"Dizin yapısı hatası: {e}")
        return False

def create_turkish_main_service():
    """Create main Turkish storyteller service"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Ana Türkçe servis oluşturuluyor...")
        
        main_service_code = '''#!/usr/bin/env python3
"""
Turkish StorytellerPi Main Service
Integrated service for Turkish storytelling with remote processing
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config_validator import ConfigValidator
from service_manager import ServiceManager
from storyteller_llm_turkish import TurkishStorytellerLLM
from stt_service_turkish import TurkishSTTService
from tts_service_turkish import TurkishTTSService
from wake_word_detector import WakeWordDetector
from web_interface import WebInterface

class TurkishStorytellerMain:
    """Main Turkish StorytellerPi service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_validator = ConfigValidator()
        self.service_manager = ServiceManager()
        self.is_running = False
        self.services = {}
        
    async def initialize(self):
        """Initialize all Turkish services"""
        try:
            self.logger.info("🎭 Turkish StorytellerPi başlatılıyor...")
            
            # Validate configuration
            config_valid = self.config_validator.validate_config()
            if not config_valid:
                self.logger.error("❌ Konfigürasyon doğrulaması başarısız!")
                return False
            
            # Initialize services
            services_config = {
                'storyteller_llm': TurkishStorytellerLLM,
                'stt_service': TurkishSTTService,
                'tts_service': TurkishTTSService,
                'wake_word_detector': WakeWordDetector,
                'web_interface': WebInterface
            }
            
            # Start service manager
            success = await self.service_manager.initialize_services(services_config)
            if not success:
                self.logger.error("❌ Servis yöneticisi başlatılamadı!")
                return False
            
            self.services = self.service_manager.get_services()
            self.is_running = True
            
            self.logger.info("✅ Turkish StorytellerPi başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Başlatma hatası: {e}")
            return False
    
    async def run(self):
        """Run the main service loop"""
        try:
            while self.is_running:
                await asyncio.sleep(1)
                
                # Health check
                if not self.service_manager.health_check():
                    self.logger.warning("⚠️ Servis sağlığı kontrolü başarısız!")
                    # Restart services if needed
                    await self.service_manager.restart_failed_services()
                
        except Exception as e:
            self.logger.error(f"Ana döngü hatası: {e}")
    
    async def cleanup(self):
        """Clean up all services"""
        try:
            self.logger.info("🧹 Turkish StorytellerPi temizleniyor...")
            
            self.is_running = False
            
            if self.service_manager:
                await self.service_manager.cleanup_all_services()
            
            self.logger.info("✅ Temizlik tamamlandı!")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info(f"Sistem sinyali alındı: {signum}")
        self.is_running = False

async def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('storyteller_turkish.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Create main service
    storyteller = TurkishStorytellerMain()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, storyteller.signal_handler)
    signal.signal(signal.SIGTERM, storyteller.signal_handler)
    
    try:
        # Initialize
        success = await storyteller.initialize()
        if not success:
            logger.error("❌ Başlatma başarısız!")
            return 1
        
        # Run
        await storyteller.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        return 1
    finally:
        await storyteller.cleanup()
    
    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
'''
        
        # Write main service
        with open('main/storyteller_main_turkish.py', 'w', encoding='utf-8') as f:
            f.write(main_service_code)
        
        logger.info("✅ Ana Türkçe servis oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"Ana servis oluşturma hatası: {e}")
        return False

def create_systemd_service():
    """Create systemd service file for Turkish StorytellerPi"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Systemd servisi oluşturuluyor...")
        
        service_content = """[Unit]
Description=Turkish StorytellerPi Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/storytellerpi
Environment=PYTHONPATH=/opt/storytellerpi
ExecStart=/usr/bin/python3 /opt/storytellerpi/main/storyteller_main_turkish.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10

# Environment
Environment=LANG=tr_TR.UTF-8
Environment=LC_ALL=tr_TR.UTF-8

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=storytellerpi-turkish

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/storytellerpi/logs
ReadWritePaths=/opt/storytellerpi/models
ReadWritePaths=/opt/storytellerpi/credentials

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        with open('storytellerpi-turkish.service', 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        logger.info("✅ Systemd servisi oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"Systemd servisi hatası: {e}")
        return False

def create_startup_script():
    """Create startup script for Turkish StorytellerPi"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Başlangıç scripti oluşturuluyor...")
        
        startup_script = '''#!/bin/bash
# Turkish StorytellerPi Startup Script
# Türkçe hikaye asistanı başlatma scripti

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

print_color $BLUE "🎭 Turkish StorytellerPi Başlatılıyor..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_color $RED "❌ Bu script root olarak çalıştırılmamalı!"
    exit 1
fi

# Set Turkish locale
export LANG=tr_TR.UTF-8
export LC_ALL=tr_TR.UTF-8

# Change to installation directory
cd /opt/storytellerpi

# Check if .env file exists
if [ ! -f .env ]; then
    print_color $YELLOW "⚠️ .env dosyası bulunamadı!"
    print_color $YELLOW "Lütfen API anahtarlarınızı konfigüre edin."
    exit 1
fi

# Check if credentials exist
if [ ! -f credentials/google-credentials.json ]; then
    print_color $YELLOW "⚠️ Google credentials dosyası bulunamadı!"
    print_color $YELLOW "Lütfen Google Cloud credentials JSON dosyasını yükleyin."
    exit 1
fi

# Create logs directory
mkdir -p logs

# Check if virtual environment exists
if [ ! -d venv ]; then
    print_color $YELLOW "⚠️ Python virtual environment bulunamadı, oluşturuluyor..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
print_color $BLUE "📦 Gereksinimler yükleniyor..."
pip install -r requirements_turkish_lightweight.txt

# Set permissions
chmod +x main/storyteller_main_turkish.py

# Start the service
print_color $GREEN "🚀 Turkish StorytellerPi başlatılıyor..."
python3 main/storyteller_main_turkish.py

print_color $GREEN "✅ Turkish StorytellerPi başarıyla başlatıldı!"
print_color $BLUE "🌐 Web arayüzü: http://localhost:5000"
print_color $BLUE "🎤 Uyandırma kelimesi: 'Merhaba Asistan'"
'''
        
        # Write startup script
        with open('start_turkish_storyteller.sh', 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod('start_turkish_storyteller.sh', 0o755)
        
        logger.info("✅ Başlangıç scripti oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"Başlangıç scripti hatası: {e}")
        return False

def create_api_keys_guide():
    """Create API keys configuration guide"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("API anahtarları kılavuzu oluşturuluyor...")
        
        guide_content = '''# Turkish StorytellerPi API Anahtarları Kılavuzu

Bu kılavuz, Turkish StorytellerPi için gerekli API anahtarlarını nasıl alacağınızı açıklar.

## 🔑 Gerekli API Anahtarları

### 1. OpenAI API Anahtarı (Hikaye Üretimi)
- **Amaç**: GPT-4 ile Türkçe hikaye üretimi
- **Nasıl Alınır**:
  1. https://platform.openai.com/api-keys adresine gidin
  2. OpenAI hesabınızla giriş yapın
  3. "Create new secret key" butonuna tıklayın
  4. Anahtarı kopyalayın ve güvenli bir yerde saklayın
- **Maliyet**: Token başına ücretlendirme (~$0.03/1K token)
- **Kullanım**: Çocuk dostu Türkçe hikaye üretimi

### 2. ElevenLabs API Anahtarı (Ses Sentezi)
- **Amaç**: Yüksek kaliteli Türkçe ses sentezi
- **Nasıl Alınır**:
  1. https://elevenlabs.io/app/settings/api-keys adresine gidin
  2. ElevenLabs hesabınızla giriş yapın
  3. "Generate" butonuna tıklayarak yeni anahtar oluşturun
  4. Anahtarı kopyalayın
- **Maliyet**: Karakter başına ücretlendirme (~$0.30/1K karakter)
- **Kullanım**: Çocuk dostu kadın ses ile hikaye anlatımı

### 3. ElevenLabs Türkçe Ses ID'si
- **Amaç**: Hikaye anlatımı için uygun Türkçe ses seçimi
- **Nasıl Alınır**:
  1. https://elevenlabs.io/app/voice-library adresine gidin
  2. "Turkish" dil filtresini seçin
  3. Hikaye anlatımı için uygun kadın ses bulun
  4. Ses ID'sini kopyalayın
- **Öneriler**:
  - Genç yetişkin kadın sesi tercih edin
  - "Storytelling" veya "Narration" etiketli sesleri seçin
  - Ses örneklerini dinleyip en uygun olanı seçin

### 4. Google Cloud Speech API (Konuşma Tanıma)
- **Amaç**: Türkçe konuşma tanıma
- **Nasıl Alınır**:
  1. https://cloud.google.com/speech-to-text/docs/before-you-begin adresine gidin
  2. Google Cloud Console'da yeni proje oluşturun
  3. Speech-to-Text API'sini etkinleştirin
  4. Service account oluşturun ve JSON anahtarını indirin
- **Maliyet**: Dakika başına ücretlendirme (~$0.024/dakika)
- **Kullanım**: Çocuğun Türkçe konuşmasını tanıma

### 5. Porcupine Wake Word API (Uyandırma Kelimesi)
- **Amaç**: "Merhaba Asistan" uyandırma kelimesi tanıma
- **Nasıl Alınır**:
  1. https://console.picovoice.ai/ adresine gidin
  2. Picovoice hesabınızla giriş yapın
  3. "Access Keys" sekmesinden yeni anahtar oluşturun
  4. Anahtarı kopyalayın
- **Maliyet**: Ücretsiz katman mevcut (aylık 1000 sorgu)
- **Kullanım**: Yerel uyandırma kelimesi tanıma

## 📝 Konfigürasyon Adımları

### 1. .env Dosyasını Düzenleyin
```bash
# .env dosyasını açın
nano .env

# API anahtarlarınızı girin
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=your-turkish-voice-id-here
PORCUPINE_ACCESS_KEY=your-porcupine-key-here
```

### 2. Google Credentials JSON Dosyasını Yükleyin
```bash
# Google credentials dosyasını kopyalayın
cp /path/to/your/google-credentials.json credentials/google-credentials.json

# İzinleri ayarlayın
chmod 600 credentials/google-credentials.json
```

### 3. Konfigürasyonu Test Edin
```bash
# Test scriptini çalıştırın
python3 main/storyteller_llm_turkish.py
python3 main/stt_service_turkish.py
python3 main/tts_service_turkish.py
```

## 💰 Maliyet Hesaplama

### Günlük Kullanım Tahmini (30 hikaye)
- **OpenAI GPT-4**: ~$1.50/gün
- **ElevenLabs TTS**: ~$0.90/gün
- **Google Speech**: ~$0.50/gün
- **Porcupine**: Ücretsiz
- **TOPLAM**: ~$2.90/gün

### Aylık Maliyet
- **Günlük kullanım**: ~$2.90
- **Aylık toplam**: ~$87.00

## 🔒 Güvenlik Uyarıları

1. **API anahtarlarını asla paylaşmayın**
2. **Dosya izinlerini 600 yapın**: `chmod 600 .env`
3. **Anahtarları Git'e commit etmeyin**
4. **Düzenli olarak anahtarları yenileyin**
5. **Kullanım limitlerini takip edin**

## 🆘 Sorun Giderme

### API Anahtarı Hatası
```
Error: Invalid API key
```
- API anahtarının doğru kopyalandığından emin olun
- Boşluk ve özel karakterler olmadığını kontrol edin
- Anahtarın aktif olduğunu doğrulayın

### Ses ID Hatası
```
Error: Voice not found
```
- ElevenLabs ses ID'sinin doğru olduğundan emin olun
- Ses'in Türkçe desteklediğini kontrol edin
- Alternatif ses ID'si deneyin

### Google Credentials Hatası
```
Error: Could not load credentials
```
- JSON dosyasının doğru konumda olduğundan emin olun
- Dosya izinlerini kontrol edin
- JSON formatının geçerli olduğunu doğrulayın

## 📞 Destek

Sorunlar için:
1. Log dosyalarını kontrol edin: `tail -f logs/storyteller_turkish.log`
2. Test scriptlerini çalıştırın
3. API provider'ların dokümantasyonuna bakın
4. Kullanım limitlerini kontrol edin

Bu kılavuz sayesinde Turkish StorytellerPi'nizi başarıyla konfigüre edebilirsiniz! 🎭
'''
        
        # Write guide
        with open('API_KEYS_GUIDE_TR.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        logger.info("✅ API anahtarları kılavuzu oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"API kılavuzu hatası: {e}")
        return False

def main():
    """Main setup function"""
    logger = setup_logging()
    
    print("🎭" + "="*60 + "🎭")
    print("    TURKISH STORYTELLERPI COMPLETE SETUP")
    print("    5 Yaşındaki Küçük Prenses İçin Özel Kurulum")
    print("🎭" + "="*60 + "🎭")
    
    setup_steps = [
        ("📦 Hafif bağımlılıklar yükleniyor", install_lightweight_requirements),
        ("🏗️ Dizin yapısı oluşturuluyor", setup_directory_structure),
        ("🌍 Türkçe ortam konfigürasyonu", create_turkish_environment),
        ("🎭 Ana Türkçe servis oluşturuluyor", create_turkish_main_service),
        ("🔧 Systemd servisi oluşturuluyor", create_systemd_service),
        ("🚀 Başlangıç scripti oluşturuluyor", create_startup_script),
        ("🔑 API anahtarları kılavuzu oluşturuluyor", create_api_keys_guide)
    ]
    
    success_count = 0
    
    for step_name, step_function in setup_steps:
        print(f"\n{'='*60}")
        print(f"▶️ {step_name}")
        print('='*60)
        
        try:
            result = step_function()
            if result:
                print(f"✅ {step_name} - BAŞARILI")
                success_count += 1
            else:
                print(f"❌ {step_name} - BAŞARISIZ")
        except Exception as e:
            print(f"❌ {step_name} - HATA: {e}")
            logger.error(f"{step_name} hatası: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 KURULUM SONUÇLARI")
    print(f"{'='*60}")
    print(f"✅ Başarılı: {success_count}/{len(setup_steps)}")
    print(f"❌ Başarısız: {len(setup_steps) - success_count}/{len(setup_steps)}")
    
    if success_count == len(setup_steps):
        print("\n🎉 TURKISH STORYTELLERPI KURULUMU TAMAMLANDI! 🎉")
        print("\n📋 SONRAKI ADIMLAR:")
        print("1. 🔑 API anahtarlarınızı .env dosyasında konfigüre edin")
        print("2. 📄 Google credentials JSON dosyasını yükleyin")
        print("3. 🎤 Turkish ses ID'sini ElevenLabs'dan alın")
        print("4. 🚀 ./start_turkish_storyteller.sh ile başlatın")
        print("5. 🌐 Web arayüzü: http://localhost:5000")
        print("6. 🎭 Uyandırma kelimesi: 'Merhaba Asistan'")
        
        print("\n🎯 ÖZELLİKLER:")
        print("✅ Türkçe hikaye anlatımı (OpenAI GPT-4)")
        print("✅ Yüksek kaliteli Türkçe ses (ElevenLabs)")
        print("✅ Türkçe konuşma tanıma (Google Cloud)")
        print("✅ Türkçe uyandırma kelimesi (Porcupine)")
        print("✅ 5 yaşındaki kız çocuğuna özel içerik")
        print("✅ Pi Zero 2W için optimize edilmiş")
        print("✅ Tüm ağır işlemler uzak API'lerde")
        print("✅ Çocuk dostu tema ve güvenlik")
        print("✅ Prenses, peri, dostluk hikayeleri")
        print("✅ Türkçe web arayüzü")
        
        print("\n📚 DOKÜMANTASYON:")
        print("- API_KEYS_GUIDE_TR.md: API anahtarları kılavuzu")
        print("- .env: Konfigürasyon dosyası")
        print("- storyteller_turkish.log: Uygulama logları")
        
        print("\n🎭 Küçük prensesiniz artık Türkçe hikayelerin keyfini çıkarabilir! 👑")
        
    else:
        print("\n⚠️ Kurulum kısmen tamamlandı!")
        print("❌ Başarısız olan adımları tekrar deneyin")
        print("📋 Loglarda hata detaylarını kontrol edin")
    
    return 0 if success_count == len(setup_steps) else 1

if __name__ == '__main__':
    sys.exit(main())