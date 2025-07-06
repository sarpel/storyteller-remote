#!/usr/bin/env python3
"""
Turkish StorytellerPi Setup
Configures system for Turkish language support and remote processing
Optimized for 5-year-old girl with minimal local processing
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

def setup_logging():
    """Setup logging for Turkish setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup_turkish_storyteller.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def create_turkish_environment_config() -> Dict[str, str]:
    """Create Turkish-specific environment configuration"""
    logger = logging.getLogger(__name__)
    
    turkish_config = {
        # Language Configuration
        'SYSTEM_LANGUAGE': 'tr-TR',
        'SYSTEM_LOCALE': 'tr_TR.UTF-8',
        'STORY_LANGUAGE': 'turkish',
        'CHILD_NAME': 'Küçük Prenses',  # Little Princess - can be customized
        'CHILD_AGE': '5',
        'CHILD_GENDER': 'kız',  # girl
        
        # Wake Word Configuration (Turkish)
        'WAKE_WORD': 'merhaba asistan',  # Hello Assistant
        'WAKE_WORD_FRAMEWORK': 'porcupine',
        'WAKE_WORD_SENSITIVITY': '0.7',
        'WAKE_WORD_MODEL_PATH': '/opt/storytellerpi/models/merhaba-asistan.ppn',
        
        # Speech-to-Text Configuration (Remote Only)
        'STT_SERVICE': 'google',  # Google supports Turkish well
        'STT_LANGUAGE_CODE': 'tr-TR',
        'STT_ALTERNATIVE_LANGUAGE': 'tr',
        'STT_TIMEOUT': '10.0',
        'STT_MAX_AUDIO_LENGTH': '30.0',
        'STT_USE_LOCAL_MODELS': 'false',  # No local Whisper
        'STT_REMOTE_ONLY': 'true',
        
        # Text-to-Speech Configuration (Remote Only)
        'TTS_SERVICE': 'elevenlabs',  # ElevenLabs supports Turkish
        'TTS_LANGUAGE': 'tr',
        'TTS_VOICE_GENDER': 'female',
        'TTS_VOICE_AGE': 'young_adult',
        'TTS_VOICE_STYLE': 'storyteller',
        'TTS_VOICE_STABILITY': '0.8',
        'TTS_VOICE_SIMILARITY_BOOST': '0.7',
        'TTS_MODEL_ID': 'eleven_turbo_v2',
        'TTS_REMOTE_ONLY': 'true',
        
        # LLM Configuration (Remote Only)
        'LLM_SERVICE': 'openai',  # OpenAI GPT-4 handles Turkish well
        'LLM_MODEL': 'gpt-4',
        'LLM_LANGUAGE': 'turkish',
        'LLM_TEMPERATURE': '0.8',  # Creative storytelling
        'LLM_MAX_TOKENS': '800',
        'LLM_REMOTE_ONLY': 'true',
        
        # Child-Specific Story Configuration
        'STORY_TARGET_AUDIENCE': '5_year_old_girl',
        'STORY_CONTENT_FILTER': 'very_strict',
        'STORY_THEMES': 'prenses,peri,dostluk,macera,hayvanlar',  # princess,fairy,friendship,adventure,animals
        'STORY_LENGTH': 'short',  # 2-3 minutes
        'STORY_TONE': 'gentle_enthusiastic',
        'STORY_INCLUDE_MORAL': 'true',
        'STORY_AVOID_SCARY': 'true',
        
        # Turkish Story System Prompts
        'STORY_SYSTEM_PROMPT': '''Sen 5 yaşındaki küçük bir kız çocuğu için hikaye anlatan sevimli bir asistansın. 
        Hikayelerin hep güzel, eğitici ve yaşına uygun olmalı. Prenses hikayeleri, peri masalları, dostluk ve 
        macera hikayelerini seviyorsun. Hikayelerin kısa (2-3 dakika), anlaşılır ve her zaman güzel bir mesaj 
        içermeli. Korkunç, ürkütücü veya üzücü şeyler anlatmamalısın.''',
        
        'STORY_GREETING': 'Merhaba küçük prenses! Bugün sana güzel bir hikaye anlatmak istiyorum.',
        
        'STORY_ENDING_PHRASES': 'Ve böylece,İşte bu kadar,Hikayemiz burada bitiyor',
        
        # Audio Feedback in Turkish
        'AUDIO_FEEDBACK_ENABLED': 'true',
        'AUDIO_FEEDBACK_WAKE_WORD_TONE': '880.0',
        'AUDIO_FEEDBACK_SUCCESS_TONE': '1000.0',
        'AUDIO_FEEDBACK_ERROR_TONE': '400.0',
        
        # Performance Optimization for Pi Zero 2W
        'OPTIMIZE_FOR_PI_ZERO': 'true',
        'USE_LOCAL_MODELS': 'false',  # Everything remote
        'MEMORY_LIMIT': '300',  # MB
        'CPU_LIMIT': '80',  # Percentage
        'DISABLE_HEAVY_PROCESSING': 'true',
        
        # Web Interface in Turkish
        'WEB_LANGUAGE': 'tr',
        'WEB_TITLE': 'Hikaye Asistanı',
        'WEB_ENABLED': 'true',
        'WEB_HOST': '0.0.0.0',
        'WEB_PORT': '5000',
        'WEB_DEBUG': 'false',
        
        # System Configuration
        'INSTALL_DIR': '/opt/storytellerpi',
        'LOG_DIR': '/opt/storytellerpi/logs',
        'MODELS_DIR': '/opt/storytellerpi/models',
        'CREDENTIALS_DIR': '/opt/storytellerpi/credentials',
        'SERVICE_NAME': 'storytellerpi',
        'LOG_LEVEL': 'INFO',
        'LOG_LANGUAGE': 'turkish',
        
        # API Keys Configuration (to be filled by user)
        'OPENAI_API_KEY': 'YOUR_OPENAI_API_KEY',
        'GOOGLE_CREDENTIALS_JSON': '/opt/storytellerpi/credentials/google-credentials.json',
        'ELEVENLABS_API_KEY': 'YOUR_ELEVENLABS_API_KEY',
        'ELEVENLABS_VOICE_ID': 'YOUR_TURKISH_VOICE_ID',
        'PORCUPINE_ACCESS_KEY': 'YOUR_PORCUPINE_ACCESS_KEY'
    }
    
    logger.info("Turkish environment configuration created")
    return turkish_config

def create_turkish_web_templates():
    """Create Turkish language web templates"""
    logger = logging.getLogger(__name__)
    
    # Turkish base template
    turkish_base_template = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Hikaye Asistanı{% endblock %}</title>
    
    <!-- Turkish fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@300;400;700&family=Fredoka+One:wght@400&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #ff6b9d;
            --secondary-color: #c44569;
            --accent-color: #f8b500;
            --success-color: #26de81;
            --warning-color: #ffa502;
            --danger-color: #fc5c65;
            --light-bg: #fef7f7;
            --card-bg: #ffffff;
            --text-primary: #2c2c54;
            --text-secondary: #6c757d;
            --border-color: #ffe4e6;
            --shadow: 0 4px 6px -1px rgba(255, 107, 157, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Comfortaa', cursive;
            background: linear-gradient(135deg, #fef7f7 0%, #ffe4e6 100%);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--card-bg);
            border-radius: 20px;
            box-shadow: var(--shadow);
        }

        .header h1 {
            font-family: 'Fredoka One', cursive;
            color: var(--primary-color);
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            color: var(--text-secondary);
            font-size: 1.1em;
        }

        .card {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: var(--shadow);
            border: 2px solid var(--border-color);
        }

        .card h2 {
            color: var(--primary-color);
            margin-bottom: 15px;
            font-size: 1.4em;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            border-radius: 10px;
            margin: 10px 0;
            font-weight: 600;
        }

        .status.running {
            background: rgba(38, 222, 129, 0.1);
            color: var(--success-color);
        }

        .status.stopped {
            background: rgba(252, 92, 101, 0.1);
            color: var(--danger-color);
        }

        .status.unknown {
            background: rgba(255, 165, 2, 0.1);
            color: var(--warning-color);
        }

        .btn {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-family: 'Comfortaa', cursive;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
        }

        .btn:hover {
            background: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(196, 69, 105, 0.3);
        }

        .btn.start { background: var(--success-color); }
        .btn.stop { background: var(--danger-color); }
        .btn.restart { background: var(--warning-color); }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat {
            text-align: center;
            padding: 15px;
            background: rgba(255, 107, 157, 0.05);
            border-radius: 10px;
        }

        .stat-value {
            font-size: 2em;
            font-weight: 700;
            color: var(--primary-color);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-top: 5px;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .princess-icon {
            font-size: 1.5em;
            color: var(--accent-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-crown princess-icon"></i> Hikaye Asistanı <i class="fas fa-crown princess-icon"></i></h1>
            <p>Küçük Prenses için Özel Hikaye Anlatıcısı</p>
        </div>
        
        {% block content %}{% endblock %}
        
        <div class="footer">
            <p><i class="fas fa-heart" style="color: var(--primary-color);"></i> 5 yaşındaki prensesimiz için özel olarak hazırlandı <i class="fas fa-heart" style="color: var(--primary-color);"></i></p>
        </div>
    </div>
</body>
</html>'''

    # Turkish dashboard template
    turkish_dashboard_template = '''{% extends "base.html" %}

{% block title %}Kontrol Paneli - Hikaye Asistanı{% endblock %}

{% block content %}
<!-- Servis Durumu -->
<div class="card">
    <h2>
        <i class="fas fa-heartbeat"></i>
        Servis Durumu
    </h2>
    <div class="status {{ service_status.status }}">
        <i class="fas fa-circle"></i>
        {% if service_status.status == 'running' %}
            Çalışıyor
        {% elif service_status.status == 'stopped' %}
            Durduruldu
        {% else %}
            Bilinmiyor
        {% endif %}
    </div>
    
    <div class="grid">
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-{{ 'play' if service_status.active else 'stop' }}"></i>
            </div>
            <div class="stat-label">
                Hikaye Asistanı {{ 'Aktif' if service_status.active else 'Pasif' }}
            </div>
        </div>
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-microphone"></i>
            </div>
            <div class="stat-label">Ses Dinleme</div>
        </div>
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-volume-up"></i>
            </div>
            <div class="stat-label">Hikaye Anlatma</div>
        </div>
    </div>
    
    <div style="margin-top: 20px;">
        <button class="btn start" onclick="controlService('start')">
            <i class="fas fa-play"></i> Başlat
        </button>
        <button class="btn stop" onclick="controlService('stop')">
            <i class="fas fa-stop"></i> Durdur
        </button>
        <button class="btn restart" onclick="controlService('restart')">
            <i class="fas fa-redo"></i> Yeniden Başlat
        </button>
    </div>
</div>

<!-- Sistem Bilgileri -->
<div class="card">
    <h2>
        <i class="fas fa-microchip"></i>
        Sistem Bilgileri
    </h2>
    <div class="grid">
        <div class="stat">
            <div class="stat-value">{{ system_info.cpu_percent }}%</div>
            <div class="stat-label">İşlemci Kullanımı</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ system_info.memory_percent }}%</div>
            <div class="stat-label">Bellek Kullanımı</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ system_info.disk_percent }}%</div>
            <div class="stat-label">Disk Kullanımı</div>
        </div>
    </div>
</div>

<!-- Hikaye Ayarları -->
<div class="card">
    <h2>
        <i class="fas fa-book"></i>
        Hikaye Ayarları
    </h2>
    <div class="grid">
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-crown" style="color: var(--accent-color);"></i>
            </div>
            <div class="stat-label">Prenses Hikayeleri</div>
        </div>
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-magic" style="color: var(--accent-color);"></i>
            </div>
            <div class="stat-label">Peri Masalları</div>
        </div>
        <div class="stat">
            <div class="stat-value">
                <i class="fas fa-heart" style="color: var(--accent-color);"></i>
            </div>
            <div class="stat-label">Dostluk Hikayeleri</div>
        </div>
    </div>
</div>

<!-- Ses Testi -->
<div class="card">
    <h2>
        <i class="fas fa-volume-up"></i>
        Ses Testi
    </h2>
    <p>Hikaye asistanının ses sistemini test edin:</p>
    <div style="margin-top: 15px;">
        <button class="btn" onclick="testAudio('speaker')">
            <i class="fas fa-volume-up"></i> Hoparlör Test
        </button>
        <button class="btn" onclick="testAudio('microphone')">
            <i class="fas fa-microphone"></i> Mikrofon Test
        </button>
        <button class="btn" onclick="testAudio('greeting')">
            <i class="fas fa-comments"></i> Karşılama Test
        </button>
    </div>
</div>

<!-- Son Loglar -->
{% if recent_logs %}
<div class="card">
    <h2>
        <i class="fas fa-file-alt"></i>
        Son Aktiviteler
    </h2>
    <div style="max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;">
        {% for log in recent_logs %}
        <div style="margin-bottom: 5px; font-size: 0.9em;">
            <strong>{{ log.timestamp }}</strong> - {{ log.message }}
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}

<script>
function controlService(action) {
    const actionNames = {
        'start': 'başlatılıyor',
        'stop': 'durduruluyor',
        'restart': 'yeniden başlatılıyor'
    };
    
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + actionNames[action];
    button.disabled = true;
    
    fetch(`/api/service/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Başarılı: ' + data.message, 'success');
        } else {
            showNotification('Hata: ' + data.message, 'error');
        }
        setTimeout(() => {
            location.reload();
        }, 1000);
    })
    .catch(error => {
        showNotification('Bağlantı hatası: ' + error, 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function testAudio(type) {
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Test ediliyor...';
    button.disabled = true;
    
    fetch(`/api/test/${type}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Test başarılı: ' + data.message, 'success');
        } else {
            showNotification('Test başarısız: ' + data.message, 'error');
        }
        button.innerHTML = originalText;
        button.disabled = false;
    })
    .catch(error => {
        showNotification('Test hatası: ' + error, 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        max-width: 300px;
        background: ${type === 'success' ? 'var(--success-color)' : 'var(--danger-color)'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Auto-refresh status every 30 seconds
setInterval(() => {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            // Update status indicators
            console.log('Status updated:', data);
        })
        .catch(error => console.error('Status update error:', error));
}, 30000);
</script>
{% endblock %}'''

    # Create templates directory
    templates_dir = Path("main/templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Write Turkish templates
    with open(templates_dir / "base_turkish.html", 'w', encoding='utf-8') as f:
        f.write(turkish_base_template)
    
    with open(templates_dir / "dashboard_turkish.html", 'w', encoding='utf-8') as f:
        f.write(turkish_dashboard_template)
    
    logger.info("Turkish web templates created")
    return True

def create_turkish_system_prompts():
    """Create Turkish system prompts for storytelling"""
    logger = logging.getLogger(__name__)
    
    turkish_prompts = {
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
            "Selam küçük prenses! Hangi konuda hikaye istiyorsun?"
        ],
        
        'story_starters': [
            "Bir zamanlar, çok uzak diyarlarda...",
            "Masallar ülkesinde, güzel bir prenses varmış...",
            "Çok güzel bir ormanda, sevimli hayvanlar yaşarmış...",
            "Büyülü bir krallıkta, iyi kalpli bir peri varmış..."
        ],
        
        'story_endings': [
            "Ve işte hikayemiz böyle bitiyor küçük prenses!",
            "Hikayemiz burada son buluyor. Çok güzeldi değil mi?",
            "Ve böylece mutlu mesut yaşamışlar. Hikaye böyle bitiyor prensesim!",
            "İşte bu kadar güzel hikayemiz! Yarın yeni bir hikaye anlatırım sana!"
        ],
        
        'moral_lessons': [
            "dostluğun ne kadar önemli olduğunu",
            "paylaşmanın güzel olduğunu",
            "iyiliğin her zaman kazandığını",
            "sevginin her şeyi yendiğini",
            "cesur olmanın önemini",
            "başkalarına yardım etmenin güzel olduğunu"
        ]
    }
    
    # Create prompts directory
    prompts_dir = Path("main/prompts")
    prompts_dir.mkdir(exist_ok=True)
    
    # Write Turkish prompts
    with open(prompts_dir / "turkish_prompts.py", 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python3
'''
Turkish Language Prompts for StorytellerPi
Optimized for 5-year-old girl audience
'''

import random

TURKISH_PROMPTS = {repr(turkish_prompts)}

def get_random_greeting():
    return random.choice(TURKISH_PROMPTS['greeting_prompts'])

def get_random_story_starter():
    return random.choice(TURKISH_PROMPTS['story_starters'])

def get_random_story_ending():
    return random.choice(TURKISH_PROMPTS['story_endings'])

def get_random_moral_lesson():
    return random.choice(TURKISH_PROMPTS['moral_lessons'])

def get_main_system_prompt():
    return TURKISH_PROMPTS['main_system_prompt']

def create_story_prompt(topic=None, theme=None):
    '''Create a story prompt based on topic and theme'''
    starter = get_random_story_starter()
    moral = get_random_moral_lesson()
    
    prompt = f'''{{get_main_system_prompt()}}
    
    GÖREV: Küçük prenses için bir hikaye anlat.
    
    Hikaye şöyle başlasın: "{starter}"
    
    {"Konu: " + topic if topic else ""}
    {"Tema: " + theme if theme else ""}
    
    Hikayenin sonunda {moral} öğretmelisin.
    
    Hikayen 150-200 kelime olmalı ve "{get_random_story_ending()}" şeklinde bitmelisin.
    '''
    
    return prompt
""")
    
    logger.info("Turkish system prompts created")
    return True

def optimize_for_remote_processing():
    """Create configuration optimized for remote processing only"""
    logger = logging.getLogger(__name__)
    
    # Create lightweight requirements.txt (no heavy local models)
    lightweight_requirements = """
# Turkish StorytellerPi - Remote Processing Only
# Optimized for Pi Zero 2W with minimal local processing

# Core Framework
flask==2.3.3
flask-socketio==5.3.6
python-dotenv==1.0.0

# System Monitoring
psutil==5.9.6

# Audio (minimal for wake word only)
pyaudio==0.2.11
numpy==1.24.3

# Remote API Clients
openai==1.3.7
google-cloud-speech==2.21.0
elevenlabs==0.2.26

# Wake Word (Porcupine only)
pvporcupine==2.2.1

# Utilities
requests==2.31.0
urllib3==2.0.7
aiohttp==3.9.0

# Configuration
pyyaml==6.0.1
jsonschema==4.17.3

# NO LOCAL MODELS:
# - No whisper or speech recognition models
# - No local LLM models
# - No tensorflow/pytorch
# - No large ML libraries
"""
    
    with open("requirements_turkish.txt", 'w', encoding='utf-8') as f:
        f.write(lightweight_requirements)
    
    logger.info("Lightweight requirements created for remote processing")
    return True

def create_turkish_api_configuration():
    """Create Turkish-specific API configuration"""
    logger = logging.getLogger(__name__)
    
    api_config = {
        'google_stt': {
            'language_code': 'tr-TR',
            'alternative_language_codes': ['tr'],
            'model': 'latest_short',
            'use_enhanced': True,
            'enable_automatic_punctuation': True,
            'enable_word_time_offsets': False,
            'sample_rate_hertz': 16000,
            'audio_channel_count': 1
        },
        
        'elevenlabs_tts': {
            'model_id': 'eleven_turbo_v2',
            'voice_settings': {
                'stability': 0.8,
                'similarity_boost': 0.7,
                'style': 0.3,
                'use_speaker_boost': True
            },
            'language_code': 'tr',
            'output_format': 'mp3_44100_128'
        },
        
        'openai_llm': {
            'model': 'gpt-4',
            'temperature': 0.8,
            'max_tokens': 800,
            'top_p': 0.9,
            'frequency_penalty': 0.1,
            'presence_penalty': 0.1,
            'language': 'tr'
        },
        
        'porcupine_wake_word': {
            'access_key': 'YOUR_PORCUPINE_ACCESS_KEY',
            'model_path': '/opt/storytellerpi/models/merhaba-asistan.ppn',
            'sensitivity': 0.7,
            'keywords': ['merhaba asistan']
        }
    }
    
    # Create API configuration file
    api_config_dir = Path("main/config")
    api_config_dir.mkdir(exist_ok=True)
    
    with open(api_config_dir / "turkish_api_config.py", 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python3
'''
Turkish API Configuration for StorytellerPi
Remote processing configuration optimized for Turkish language
'''

import json

TURKISH_API_CONFIG = {repr(api_config)}

def get_google_stt_config():
    return TURKISH_API_CONFIG['google_stt']

def get_elevenlabs_tts_config():
    return TURKISH_API_CONFIG['elevenlabs_tts']

def get_openai_llm_config():
    return TURKISH_API_CONFIG['openai_llm']

def get_porcupine_config():
    return TURKISH_API_CONFIG['porcupine_wake_word']

def get_full_config():
    return TURKISH_API_CONFIG
""")
    
    logger.info("Turkish API configuration created")
    return True

def create_credentials_template():
    """Create credentials template with Turkish instructions"""
    logger = logging.getLogger(__name__)
    
    credentials_template = """# StorytellerPi API Anahtarları
# Turkish StorytellerPi için gerekli API anahtarları

# OpenAI API Anahtarı (Hikaye üretimi için)
# https://platform.openai.com/api-keys adresinden alabilirsiniz
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Anahtarı (Türkçe ses sentezi için)
# https://elevenlabs.io/app/settings/api-keys adresinden alabilirsiniz
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# ElevenLabs Türkçe Ses ID'si
# https://elevenlabs.io/app/voice-library adresinden Türkçe ses seçin
ELEVENLABS_VOICE_ID=your_turkish_voice_id_here

# Google Cloud Speech API (Türkçe konuşma tanıma için)
# https://cloud.google.com/speech-to-text/docs/before-you-begin
GOOGLE_APPLICATION_CREDENTIALS=/opt/storytellerpi/credentials/google-credentials.json

# Porcupine Wake Word API Anahtarı (Türkçe uyandırma kelimesi için)
# https://console.picovoice.ai/ adresinden alabilirsiniz
PORCUPINE_ACCESS_KEY=your_porcupine_access_key_here

# ÖNEMLI NOTLAR:
# 1. Bu dosyayı güvenli tutun
# 2. API anahtarlarınızı kimseyle paylaşmayın
# 3. Dosya izinlerini 600 yapın: chmod 600 credentials.env
# 4. Google credentials için JSON dosyasını da yükleyin
"""
    
    # Create credentials directory
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)
    
    with open(credentials_dir / "credentials_template.env", 'w', encoding='utf-8') as f:
        f.write(credentials_template)
    
    # Create Google credentials placeholder
    google_credentials_template = """{
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "your-private-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n",
    "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
    "client_id": "your-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
}"""
    
    with open(credentials_dir / "google-credentials-template.json", 'w', encoding='utf-8') as f:
        f.write(google_credentials_template)
    
    logger.info("Credentials template created")
    return True

def main():
    """Main Turkish setup function"""
    logger = setup_logging()
    logger.info("Turkish StorytellerPi kurulumu başlatılıyor...")
    
    setup_steps = [
        ("Türkçe ortam konfigürasyonu", create_turkish_environment_config),
        ("Türkçe web arayüzü şablonları", create_turkish_web_templates),
        ("Türkçe sistem komutları", create_turkish_system_prompts),
        ("Uzak işleme optimizasyonu", optimize_for_remote_processing),
        ("Türkçe API konfigürasyonu", create_turkish_api_configuration),
        ("Kimlik bilgileri şablonu", create_credentials_template)
    ]
    
    for step_name, step_function in setup_steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"Adım: {step_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = step_function()
            if result:
                logger.info(f"✅ {step_name} başarıyla tamamlandı")
            else:
                logger.error(f"❌ {step_name} başarısız oldu")
                return 1
        except Exception as e:
            logger.error(f"❌ {step_name} hatası: {e}")
            return 1
    
    # Write Turkish environment file
    logger.info("\nTürkçe .env dosyası oluşturuluyor...")
    turkish_config = create_turkish_environment_config()
    
    with open(".env_turkish", 'w', encoding='utf-8') as f:
        f.write("# Turkish StorytellerPi Environment Configuration\n")
        f.write("# 5 yaşındaki küçük prenses için özel konfigürasyon\n\n")
        
        for key, value in turkish_config.items():
            f.write(f"{key}={value}\n")
    
    # Final instructions
    logger.info("\n" + "="*60)
    logger.info("🎉 TÜRKÇE STORYTELLERPİ KURULUMU TAMAMLANDI! 🎉")
    logger.info("="*60)
    logger.info("\nSONRAKİ ADIMLAR:")
    logger.info("1. .env_turkish dosyasını .env olarak kopyalayın")
    logger.info("2. credentials/credentials_template.env dosyasını doldurun")
    logger.info("3. Google credentials JSON dosyasını yükleyin")
    logger.info("4. Sistemi çalıştırın: python3 setup_storyteller_pi.py")
    logger.info("5. Web arayüzüne erişin: http://PI_IP:5000")
    logger.info("\nÖZELLİKLER:")
    logger.info("✅ Türkçe hikaye anlatımı")
    logger.info("✅ 5 yaşındaki kız çocuğuna özel")
    logger.info("✅ Uzak işleme (Pi Zero 2W için optimize)")
    logger.info("✅ Türkçe web arayüzü")
    logger.info("✅ Sadece Porcupine wake word (yerel)")
    logger.info("✅ Prenses, peri, dostluk hikayeleri")
    logger.info("\nNOT: Tüm ağır işlemler uzak API'ler üzerinden yapılır!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())