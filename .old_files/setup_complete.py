#!/usr/bin/env python3
"""
StorytellerPi Complete Setup Script
Multi-language support with Turkish optimization
All-in-one setup for hardware, software, and services
"""

import os
import sys
import asyncio
import logging
import subprocess
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import platform
import re
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StorytellerPiSetup:
    """Complete setup manager for StorytellerPi system"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.install_dir = Path("/opt/storytellerpi")
        self.venv_dir = self.install_dir / "venv"
        self.current_user = os.getenv("USER", "pi")
        self.service_name = "storytellerpi"
        
        # Hardware detection
        self.pi_model = "unknown"
        self.pi_audio_device = "default"
        self.os_type = "unknown"
        self.audio_setup_type = "default"
        
        # Language configuration
        self.language = "turkish"
        self.system_language = "tr-TR"
        self.child_name = "Küçük Prenses"
        self.child_age = 5
        self.child_gender = "kız"
        
        # Setup status
        self.setup_steps = {
            'hardware_detection': False,
            'system_update': False,
            'packages_installed': False,
            'audio_configured': False,
            'python_environment': False,
            'dependencies_installed': False,
            'project_structure': False,
            'environment_file': False,
            'credentials_templates': False,
            'systemd_service': False,
            'final_configuration': False
        }
        
        logger.info("StorytellerPi Setup Manager initialized")
    
    def log_info(self, message: str):
        """Log info message"""
        logger.info(f"🔧 {message}")
        print(f"[INFO] {message}")
    
    def log_success(self, message: str):
        """Log success message"""
        logger.info(f"✅ {message}")
        print(f"[SUCCESS] {message}")
    
    def log_warning(self, message: str):
        """Log warning message"""
        logger.warning(f"⚠️ {message}")
        print(f"[WARNING] {message}")
    
    def log_error(self, message: str):
        """Log error message"""
        logger.error(f"❌ {message}")
        print(f"[ERROR] {message}")
    
    def run_command(self, command: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """Run system command"""
        try:
            self.log_info(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {command}")
            self.log_error(f"Error: {e.stderr}")
            raise
    
    def check_root(self):
        """Check if running as root"""
        if os.geteuid() == 0:
            self.log_error("Bu script root olarak çalıştırılmamalı!")
            sys.exit(1)
    
    def check_sudo(self):
        """Check sudo availability"""
        try:
            subprocess.run(["sudo", "-n", "true"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.log_error("Sudo erişimi gerekli!")
            sys.exit(1)
    
    def detect_pi_model(self):
        """Detect Raspberry Pi model"""
        self.log_info("Raspberry Pi modeli tespit ediliyor...")
        
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
            
            if "Zero 2" in content:
                self.pi_model = "pi_zero_2w"
                self.pi_audio_device = "iqaudio_codec"
                self.log_success("Raspberry Pi Zero 2W tespit edildi")
            elif "Pi 5" in content:
                self.pi_model = "pi_5"
                self.pi_audio_device = "waveshare_usb"
                self.log_success("Raspberry Pi 5 tespit edildi")
            elif "Pi 4" in content:
                self.pi_model = "pi_4"
                self.pi_audio_device = "waveshare_usb"
                self.log_success("Raspberry Pi 4 tespit edildi")
            else:
                self.pi_model = "unknown"
                self.pi_audio_device = "default"
                self.log_warning("Bilinmeyen Pi modeli tespit edildi")
                
        except Exception as e:
            self.log_error(f"Pi model tespiti başarısız: {e}")
            self.pi_model = "unknown"
    
    def detect_os_type(self):
        """Detect operating system type"""
        self.log_info("İşletim sistemi tespit ediliyor...")
        
        if Path("/etc/dietpi/dietpi-banner").exists():
            self.os_type = "dietpi"
            self.log_success("DietPi tespit edildi")
        elif Path("/etc/rpi-issue").exists():
            self.os_type = "raspios"
            self.log_success("Raspberry Pi OS tespit edildi")
        elif Path("/etc/debian_version").exists():
            self.os_type = "debian"
            self.log_success("Debian tabanlı sistem tespit edildi")
        else:
            self.os_type = "unknown"
            self.log_warning("Bilinmeyen işletim sistemi")
    
    def setup_audio_configuration(self):
        """Setup audio configuration type"""
        self.log_info("Ses konfigürasyonu belirleniyor...")
        
        config_map = {
            ("pi_zero_2w", "dietpi"): "iqaudio_dietpi",
            ("pi_zero_2w", "raspios"): "iqaudio_raspios",
            ("pi_5", "dietpi"): "waveshare_dietpi",
            ("pi_5", "raspios"): "waveshare_raspios",
            ("pi_4", "dietpi"): "waveshare_dietpi",
            ("pi_4", "raspios"): "waveshare_raspios"
        }
        
        self.audio_setup_type = config_map.get((self.pi_model, self.os_type), "default")
        self.log_info(f"Ses konfigürasyonu: {self.audio_setup_type}")
    
    def detect_hardware(self):
        """Detect hardware configuration"""
        self.log_info("Donanım tespiti başlatılıyor...")
        
        self.detect_pi_model()
        self.detect_os_type()
        self.setup_audio_configuration()
        
        self.setup_steps['hardware_detection'] = True
        self.log_success("Donanım tespiti tamamlandı")
    
    def update_system(self):
        """Update system packages"""
        self.log_info("Sistem paketleri güncelleniyor...")
        
        try:
            self.run_command("sudo apt-get update -y")
            self.run_command("sudo apt-get upgrade -y")
            
            self.setup_steps['system_update'] = True
            self.log_success("Sistem güncellemeleri tamamlandı")
            
        except Exception as e:
            self.log_error(f"Sistem güncellemesi başarısız: {e}")
            raise
    
    def install_system_packages(self):
        """Install required system packages"""
        self.log_info("Sistem paketleri yükleniyor...")
        
        # Base packages
        base_packages = [
            "git", "curl", "wget", "python3", "python3-pip", "python3-venv",
            "python3-dev", "build-essential", "pkg-config", "libffi-dev",
            "libssl-dev", "libjpeg-dev", "zlib1g-dev", "libtiff5-dev",
            "libopenjp2-7-dev", "libfreetype6-dev", "liblcms2-dev",
            "libwebp-dev", "libasound2-dev", "portaudio19-dev",
            "libsndfile1-dev", "systemd", "vim", "nano", "htop", "tree", "jq"
        ]
        
        # OS-specific packages
        os_packages = {
            "dietpi": ["alsa-utils", "alsa-tools", "libasound2-plugins"],
            "raspios": ["pulseaudio", "pulseaudio-utils", "alsa-utils", "alsa-tools", "libasound2-plugins"]
        }
        
        # Audio hardware packages
        audio_packages = {
            "iqaudio_codec": ["i2c-tools", "device-tree-compiler"],
            "waveshare_usb": ["usb-modeswitch", "usb-modeswitch-data"]
        }
        
        # Combine packages
        packages = base_packages.copy()
        packages.extend(os_packages.get(self.os_type, []))
        packages.extend(audio_packages.get(self.pi_audio_device, []))
        
        # Install packages
        for package in packages:
            try:
                # Check if package is already installed
                result = self.run_command(f"dpkg -l | grep '^ii  {package} '", check=False)
                if result.returncode != 0:
                    self.log_info(f"Installing: {package}")
                    self.run_command(f"sudo apt-get install -y {package}")
                else:
                    self.log_info(f"Already installed: {package}")
            except Exception as e:
                self.log_warning(f"Failed to install {package}: {e}")
        
        self.setup_steps['packages_installed'] = True
        self.log_success("Sistem paketleri yüklendi")
    
    def configure_audio_iqaudio_dietpi(self):
        """Configure IQAudio Codec for DietPi"""
        self.log_info("IQAudio Codec DietPi konfigürasyonu...")
        
        # Boot config
        boot_config = """
# IQAudio Codec Zero HAT configuration
dtoverlay=iqaudio-codec
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
"""
        
        with open("/tmp/boot_config_append.txt", "w") as f:
            f.write(boot_config)
        
        self.run_command("sudo sh -c 'cat /tmp/boot_config_append.txt >> /boot/config.txt'")
        
        # ALSA configuration
        alsa_config = """pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
"""
        
        with open("/tmp/asound.conf", "w") as f:
            f.write(alsa_config)
        
        self.run_command("sudo cp /tmp/asound.conf /etc/asound.conf")
        
        # Module loading
        self.run_command("sudo sh -c 'echo \"snd_soc_iqaudio_codec\" >> /etc/modules'")
        
        self.log_success("IQAudio DietPi konfigürasyonu tamamlandı")
    
    def configure_audio_iqaudio_raspios(self):
        """Configure IQAudio Codec for Raspberry Pi OS"""
        self.log_info("IQAudio Codec Raspberry Pi OS konfigürasyonu...")
        
        # Boot config
        boot_config = """
# IQAudio Codec Zero HAT configuration
dtoverlay=iqaudio-codec
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
"""
        
        with open("/tmp/boot_config_append.txt", "w") as f:
            f.write(boot_config)
        
        self.run_command("sudo sh -c 'cat /tmp/boot_config_append.txt >> /boot/config.txt'")
        
        # ALSA configuration
        alsa_config = f"""pcm.!default {{
    type pulse
    server unix:/run/user/{os.getuid()}/pulse/native
}}

ctl.!default {{
    type pulse
    server unix:/run/user/{os.getuid()}/pulse/native
}}

pcm.hw_default {{
    type hw
    card 0
    device 0
}}

ctl.hw_default {{
    type hw
    card 0
}}
"""
        
        with open("/tmp/asound.conf", "w") as f:
            f.write(alsa_config)
        
        self.run_command("sudo cp /tmp/asound.conf /etc/asound.conf")
        
        # PulseAudio configuration
        pulse_config_dir = Path.home() / ".config" / "pulse"
        pulse_config_dir.mkdir(parents=True, exist_ok=True)
        
        pulse_config = """#!/usr/bin/pulseaudio -nF
.include /etc/pulse/default.pa
set-default-sink alsa_output.hw_0_0
set-default-source alsa_input.hw_0_0
"""
        
        with open(pulse_config_dir / "default.pa", "w") as f:
            f.write(pulse_config)
        
        self.log_success("IQAudio Raspberry Pi OS konfigürasyonu tamamlandı")
    
    def configure_audio_waveshare_dietpi(self):
        """Configure Waveshare USB Audio for DietPi"""
        self.log_info("Waveshare USB Audio DietPi konfigürasyonu...")
        
        # USB audio configuration
        alsa_config = """pcm.!default {
    type hw
    card 1
    device 0
}

ctl.!default {
    type hw
    card 1
}
"""
        
        with open("/tmp/asound.conf", "w") as f:
            f.write(alsa_config)
        
        self.run_command("sudo cp /tmp/asound.conf /etc/asound.conf")
        
        # USB audio module loading
        self.run_command("sudo sh -c 'echo \"snd_usb_audio\" >> /etc/modules'")
        
        # USB rules
        usb_rules = """SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="controlC[0-9]*", ATTR{id}=="USB*", MODE="0666"
"""
        
        with open("/tmp/99-usb-audio.rules", "w") as f:
            f.write(usb_rules)
        
        self.run_command("sudo cp /tmp/99-usb-audio.rules /etc/udev/rules.d/")
        
        self.log_success("Waveshare USB DietPi konfigürasyonu tamamlandı")
    
    def configure_audio_waveshare_raspios(self):
        """Configure Waveshare USB Audio for Raspberry Pi OS"""
        self.log_info("Waveshare USB Audio Raspberry Pi OS konfigürasyonu...")
        
        # ALSA configuration
        alsa_config = f"""pcm.!default {{
    type pulse
    server unix:/run/user/{os.getuid()}/pulse/native
}}

ctl.!default {{
    type pulse
    server unix:/run/user/{os.getuid()}/pulse/native
}}

pcm.hw_usb {{
    type hw
    card 1
    device 0
}}

ctl.hw_usb {{
    type hw
    card 1
}}
"""
        
        with open("/tmp/asound.conf", "w") as f:
            f.write(alsa_config)
        
        self.run_command("sudo cp /tmp/asound.conf /etc/asound.conf")
        
        # PulseAudio configuration
        pulse_config_dir = Path.home() / ".config" / "pulse"
        pulse_config_dir.mkdir(parents=True, exist_ok=True)
        
        pulse_config = """#!/usr/bin/pulseaudio -nF
.include /etc/pulse/default.pa
set-default-sink alsa_output.usb-*
set-default-source alsa_input.usb-*
"""
        
        with open(pulse_config_dir / "default.pa", "w") as f:
            f.write(pulse_config)
        
        # USB rules
        usb_rules = """SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="controlC[0-9]*", ATTR{id}=="USB*", MODE="0666"
"""
        
        with open("/tmp/99-usb-audio.rules", "w") as f:
            f.write(usb_rules)
        
        self.run_command("sudo cp /tmp/99-usb-audio.rules /etc/udev/rules.d/")
        
        self.log_success("Waveshare USB Raspberry Pi OS konfigürasyonu tamamlandı")
    
    def configure_audio_hardware(self):
        """Configure audio hardware"""
        self.log_info("Ses donanımı konfigürasyonu...")
        
        config_functions = {
            "iqaudio_dietpi": self.configure_audio_iqaudio_dietpi,
            "iqaudio_raspios": self.configure_audio_iqaudio_raspios,
            "waveshare_dietpi": self.configure_audio_waveshare_dietpi,
            "waveshare_raspios": self.configure_audio_waveshare_raspios
        }
        
        config_func = config_functions.get(self.audio_setup_type)
        if config_func:
            config_func()
        else:
            self.log_warning("Varsayılan ses konfigürasyonu kullanılıyor")
        
        # Test audio setup
        self.test_audio_setup()
        
        self.setup_steps['audio_configured'] = True
        self.log_success("Ses donanımı konfigürasyonu tamamlandı")
    
    def test_audio_setup(self):
        """Test audio setup"""
        self.log_info("Ses kurulumu test ediliyor...")
        
        # Test sound cards
        try:
            result = self.run_command("aplay -l", check=False)
            if result.returncode == 0:
                self.log_success("Ses kartları tespit edildi")
                print(result.stdout)
            else:
                self.log_warning("Ses kartı tespit edilemedi")
        except Exception as e:
            self.log_warning(f"Ses kartı testi başarısız: {e}")
        
        # Test ALSA
        try:
            result = self.run_command("amixer", check=False)
            if result.returncode == 0:
                self.log_success("ALSA çalışıyor")
                self.run_command("amixer sset Master 80%", check=False)
            else:
                self.log_warning("ALSA problemi")
        except Exception as e:
            self.log_warning(f"ALSA testi başarısız: {e}")
        
        # Test PulseAudio (if available)
        try:
            result = self.run_command("which pulseaudio", check=False)
            if result.returncode == 0:
                result = self.run_command("pulseaudio --check", check=False)
                if result.returncode == 0:
                    self.log_success("PulseAudio çalışıyor")
                else:
                    self.log_info("PulseAudio başlatılıyor...")
                    self.run_command("pulseaudio --start --log-target=syslog", check=False)
            else:
                self.log_info("PulseAudio mevcut değil")
        except Exception as e:
            self.log_warning(f"PulseAudio testi başarısız: {e}")
    
    def create_python_environment(self):
        """Create Python virtual environment"""
        self.log_info("Python sanal ortamı oluşturuluyor...")
        
        # Create install directory
        self.run_command(f"sudo mkdir -p {self.install_dir}")
        self.run_command(f"sudo chown -R {self.current_user}:{self.current_user} {self.install_dir}")
        
        # Create virtual environment
        self.run_command(f"python3 -m venv {self.venv_dir}")
        
        # Upgrade pip
        pip_path = self.venv_dir / "bin" / "pip"
        self.run_command(f"{pip_path} install --upgrade pip setuptools wheel")
        
        self.setup_steps['python_environment'] = True
        self.log_success("Python sanal ortamı oluşturuldu")
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        self.log_info("Python bağımlılıkları yükleniyor...")
        
        pip_path = self.venv_dir / "bin" / "pip"
        
        # Core dependencies
        dependencies = [
            "flask>=2.0.0",
            "flask-socketio>=5.0.0",
            "pyaudio>=0.2.11",
            "numpy>=1.21.0",
            "scipy>=1.7.0",
            "pygame>=2.0.0",
            "requests>=2.25.0",
            "aiohttp>=3.8.0",
            "python-dotenv>=0.19.0",
            "asyncio-mqtt>=0.11.0",
            "psutil>=5.8.0",
            "openai>=1.0.0",
            "google-generativeai>=0.3.0",
            "google-cloud-speech>=2.21.0",
            "elevenlabs>=0.2.0",
            "openwakeword>=0.5.0",
            "webrtcvad>=2.0.0",
            "librosa>=0.9.0",
            "systemd-python>=234",
            "dbus-python>=1.2.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "flake8>=4.0.0"
        ]
        
        for dep in dependencies:
            try:
                self.log_info(f"Installing: {dep}")
                self.run_command(f"{pip_path} install {dep}")
            except Exception as e:
                self.log_warning(f"Failed to install {dep}: {e}")
        
        self.setup_steps['dependencies_installed'] = True
        self.log_success("Python bağımlılıkları yüklendi")
    
    def setup_project_structure(self):
        """Setup project structure"""
        self.log_info("Proje yapısı oluşturuluyor...")
        
        # Create directories
        directories = [
            "main", "models", "credentials", "logs", "tests", "scripts"
        ]
        
        for directory in directories:
            dir_path = self.install_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Copy project files
        source_dirs = {
            "main": self.script_dir / "main",
            "models": self.script_dir / "models",
            "tests": self.script_dir / "tests",
            "scripts": self.script_dir / "scripts"
        }
        
        for dest, source in source_dirs.items():
            if source.exists():
                dest_path = self.install_dir / dest
                try:
                    shutil.copytree(source, dest_path, dirs_exist_ok=True)
                    self.log_info(f"Copied {source} to {dest_path}")
                except Exception as e:
                    self.log_warning(f"Failed to copy {source}: {e}")
        
        # Copy requirements file
        requirements_file = self.script_dir / "requirements.txt"
        if requirements_file.exists():
            shutil.copy2(requirements_file, self.install_dir / "requirements.txt")
        
        # Set permissions
        for py_file in (self.install_dir / "main").glob("*.py"):
            py_file.chmod(0o755)
        
        for py_file in (self.install_dir / "scripts").glob("*.py"):
            py_file.chmod(0o755)
        
        self.setup_steps['project_structure'] = True
        self.log_success("Proje yapısı oluşturuldu")
    
    def create_environment_file(self):
        """Create environment configuration file"""
        self.log_info("Environment dosyası oluşturuluyor...")
        
        env_content = f"""# StorytellerPi Configuration
PROJECT_NAME=StorytellerPi
PROJECT_VERSION=1.0.0
INSTALL_DIR={self.install_dir}
LOG_DIR={self.install_dir}/logs
MODELS_DIR={self.install_dir}/models
CREDENTIALS_DIR={self.install_dir}/credentials

# System Configuration
SYSTEM_LANGUAGE={self.system_language}
STORY_LANGUAGE={self.language}
PI_MODEL={self.pi_model}
PI_AUDIO_DEVICE={self.pi_audio_device}
OS_TYPE={self.os_type}
AUDIO_SETUP_TYPE={self.audio_setup_type}

# Child Configuration
CHILD_NAME={self.child_name}
CHILD_AGE={self.child_age}
CHILD_GENDER={self.child_gender}
STORY_TARGET_AUDIENCE={self.child_age}_year_old_{self.child_gender}

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1024
AUDIO_DEVICE_INDEX=0

# Wake Word Configuration
WAKE_WORD_SERVICE=openwakeword
WAKE_WORD_MODEL=hey_elsa
WAKE_WORD_THRESHOLD=0.7
WAKE_WORD_SENSITIVITY=0.5

# STT Configuration
STT_SERVICE=google
STT_LANGUAGE_CODE={self.system_language}
STT_MODEL=latest_short
STT_TIMEOUT=10.0
STT_REMOTE_ONLY=true

# LLM Configuration
LLM_SERVICE=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.8
LLM_MAX_TOKENS=800
LLM_REMOTE_ONLY=true

# TTS Configuration
TTS_SERVICE=elevenlabs
TTS_LANGUAGE={"tr" if self.language == "turkish" else "en"}
TTS_VOICE_GENDER=female
TTS_VOICE_AGE=young_adult
TTS_VOICE_STYLE=storyteller
TTS_VOICE_STABILITY=0.8
TTS_VOICE_SIMILARITY_BOOST=0.7
TTS_REMOTE_ONLY=true

# Web Interface Configuration
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false
WEB_SECRET_KEY=your-secret-key-here

# Story Configuration
STORY_THEMES={"prenses,peri,dostluk,macera,hayvanlar" if self.language == "turkish" else "princess,fairy,friendship,adventure,animals"}
STORY_LENGTH=short
STORY_TONE=gentle_enthusiastic
STORY_INCLUDE_MORAL=true
STORY_AVOID_SCARY=true
STORY_CONTENT_FILTER=very_strict

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
GOOGLE_APPLICATION_CREDENTIALS={self.install_dir}/credentials/google-credentials.json

# Service Management
SERVICE_AUTOSTART=true
SERVICE_RESTART_DELAY=5
SERVICE_MAX_RESTARTS=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE={self.install_dir}/logs/storyteller.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Security Configuration
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:*
ENABLE_AUTHENTICATION=false
"""
        
        env_file = self.install_dir / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)
        
        # Set permissions
        env_file.chmod(0o600)
        
        self.setup_steps['environment_file'] = True
        self.log_success("Environment dosyası oluşturuldu")
    
    def create_credentials_templates(self):
        """Create credential templates"""
        self.log_info("Credentials şablonları oluşturuluyor...")
        
        credentials_dir = self.install_dir / "credentials"
        
        # Google Cloud credentials template
        google_template = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
        }
        
        with open(credentials_dir / "google-credentials-template.json", "w") as f:
            json.dump(google_template, f, indent=2)
        
        # API keys template
        api_keys_template = """# StorytellerPi API Keys Configuration
# Copy this file to api-keys.txt and replace with your actual API keys

# OpenAI API Key
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key

# ElevenLabs API Key
# Get from: https://elevenlabs.io/
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Google Cloud Speech API
# Setup Google Cloud Project and enable Speech-to-Text API
# Download service account credentials JSON file
# Place in credentials/google-credentials.json

# Optional: ElevenLabs Voice ID
# Find voice ID from ElevenLabs dashboard
ELEVENLABS_VOICE_ID=your-preferred-voice-id
"""
        
        with open(credentials_dir / "api-keys-template.txt", "w") as f:
            f.write(api_keys_template)
        
        self.setup_steps['credentials_templates'] = True
        self.log_success("Credentials şablonları oluşturuldu")
    
    def create_systemd_service(self):
        """Create systemd service"""
        self.log_info("Systemd servisi oluşturuluyor...")
        
        service_content = f"""[Unit]
Description=StorytellerPi - AI Storyteller for Children
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User={self.current_user}
Group={self.current_user}
WorkingDirectory={self.install_dir}
Environment=PATH={self.venv_dir}/bin
ExecStart={self.venv_dir}/bin/python {self.install_dir}/main/storyteller_main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# Environment
EnvironmentFile={self.install_dir}/.env

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier={self.service_name}

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths={self.install_dir}
ReadOnlyPaths=/
ProtectHome=true

[Install]
WantedBy=multi-user.target
"""
        
        service_file = f"/etc/systemd/system/{self.service_name}.service"
        with open("/tmp/storytellerpi.service", "w") as f:
            f.write(service_content)
        
        self.run_command(f"sudo cp /tmp/storytellerpi.service {service_file}")
        self.run_command("sudo systemctl daemon-reload")
        self.run_command(f"sudo systemctl enable {self.service_name}.service")
        
        self.setup_steps['systemd_service'] = True
        self.log_success("Systemd servisi oluşturuldu")
    
    def finalize_configuration(self):
        """Finalize configuration"""
        self.log_info("Son konfigürasyon adımları...")
        
        # Create log directory
        log_dir = self.install_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create startup script
        startup_script = self.install_dir / "start_storyteller.sh"
        startup_content = f"""#!/bin/bash
cd {self.install_dir}
source {self.venv_dir}/bin/activate
python main/storyteller_main.py
"""
        
        with open(startup_script, "w") as f:
            f.write(startup_content)
        
        startup_script.chmod(0o755)
        
        # Create web interface startup script
        web_startup_script = self.install_dir / "start_web_interface.sh"
        web_startup_content = f"""#!/bin/bash
cd {self.install_dir}
source {self.venv_dir}/bin/activate
python main/web_interface.py
"""
        
        with open(web_startup_script, "w") as f:
            f.write(web_startup_content)
        
        web_startup_script.chmod(0o755)
        
        self.setup_steps['final_configuration'] = True
        self.log_success("Son konfigürasyon tamamlandı")
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        self.log_info("Sistem tanılaması çalıştırılıyor...")
        
        print("\n" + "="*60)
        print("StorytellerPi Sistem Tanılaması")
        print("="*60)
        
        # System information
        print(f"\n📊 Sistem Bilgileri:")
        print(f"  İşletim Sistemi: {self.os_type}")
        print(f"  Pi Modeli: {self.pi_model}")
        print(f"  Ses Cihazı: {self.pi_audio_device}")
        print(f"  Ses Konfigürasyonu: {self.audio_setup_type}")
        print(f"  Dil: {self.system_language}")
        print(f"  Çocuk: {self.child_name} ({self.child_age} yaş, {self.child_gender})")
        
        # Hardware check
        print(f"\n🔧 Donanım Kontrolü:")
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        print(f"  CPU: {line.split(':')[1].strip()}")
                        break
        except:
            pass
        
        try:
            result = self.run_command("free -h", check=False)
            if result.returncode == 0:
                memory_line = result.stdout.split('\n')[1]
                print(f"  Bellek: {memory_line.split()[1]}")
        except:
            pass
        
        # Audio check
        print(f"\n🎵 Ses Sistemi:")
        try:
            result = self.run_command("aplay -l", check=False)
            if result.returncode == 0:
                print("  ALSA: ✓ Mevcut")
                cards = result.stdout.count("card")
                print(f"  Ses kartı sayısı: {cards}")
            else:
                print("  ALSA: ✗ Problem var")
        except:
            print("  ALSA: ✗ Test edilemedi")
        
        # Python environment
        print(f"\n🐍 Python Ortamı:")
        if self.venv_dir.exists():
            print("  Sanal ortam: ✓ Mevcut")
            try:
                result = self.run_command(f"{self.venv_dir}/bin/python --version", check=False)
                if result.returncode == 0:
                    print(f"  Python: {result.stdout.strip()}")
            except:
                pass
        else:
            print("  Sanal ortam: ✗ Mevcut değil")
        
        # Project files
        print(f"\n📁 Proje Dosyaları:")
        checks = [
            ("Ana dosyalar", (self.install_dir / "main").exists()),
            ("Modeller", (self.install_dir / "models").exists()),
            ("Konfigürasyon", (self.install_dir / ".env").exists()),
            ("Credentials", (self.install_dir / "credentials").exists()),
            ("Loglar", (self.install_dir / "logs").exists())
        ]
        
        for name, exists in checks:
            status = "✓" if exists else "✗"
            print(f"  {name}: {status}")
        
        # Services
        print(f"\n⚙️ Servisler:")
        try:
            result = self.run_command(f"systemctl is-active {self.service_name}.service", check=False)
            if result.returncode == 0:
                print(f"  StorytellerPi: ✓ Çalışıyor")
            else:
                print(f"  StorytellerPi: ✗ Çalışmıyor")
        except:
            print(f"  StorytellerPi: ✗ Durum bilinmiyor")
        
        # Setup steps
        print(f"\n✅ Kurulum Adımları:")
        for step, completed in self.setup_steps.items():
            status = "✓" if completed else "✗"
            print(f"  {step.replace('_', ' ').title()}: {status}")
        
        print("\n" + "="*60)
        self.log_success("Sistem tanılaması tamamlandı")
    
    def install_complete(self):
        """Run complete installation"""
        self.log_info("StorytellerPi tam kurulumu başlatılıyor...")
        
        start_time = datetime.now()
        
        try:
            # Prerequisites
            self.check_root()
            self.check_sudo()
            
            # Main installation steps
            self.detect_hardware()
            self.update_system()
            self.install_system_packages()
            self.configure_audio_hardware()
            self.create_python_environment()
            self.install_python_dependencies()
            self.setup_project_structure()
            self.create_environment_file()
            self.create_credentials_templates()
            self.create_systemd_service()
            self.finalize_configuration()
            
            # Final summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.log_success("StorytellerPi kurulumu tamamlandı!")
            self.log_info(f"Kurulum süresi: {duration.total_seconds():.1f} saniye")
            
            print("\n" + "="*60)
            print("📋 Sonraki Adımlar:")
            print("="*60)
            print(f"1. API anahtarlarını yapılandırın: {self.install_dir}/credentials/")
            print(f"2. Konfigürasyonu kontrol edin: {self.install_dir}/.env")
            print("3. Sistemi yeniden başlatın: sudo reboot")
            print(f"4. Servisi başlatın: sudo systemctl start {self.service_name}")
            print(f"5. Durumu kontrol edin: sudo systemctl status {self.service_name}")
            print(f"6. Logları izleyin: sudo journalctl -u {self.service_name} -f")
            print(f"7. Web arayüzü: http://localhost:5000")
            print("\n" + "="*60)
            
        except Exception as e:
            self.log_error(f"Kurulum başarısız: {e}")
            raise
    
    def configure_language(self, language: str = "turkish"):
        """Configure language settings"""
        if language.lower() in ["tr", "turkish", "türkçe"]:
            self.language = "turkish"
            self.system_language = "tr-TR"
            self.child_name = "Küçük Prenses"
            self.child_gender = "kız"
        else:
            self.language = "english"
            self.system_language = "en-US"
            self.child_name = "Little Princess"
            self.child_gender = "girl"
        
        self.log_info(f"Dil ayarlandı: {self.language}")
    
    def configure_child(self, name: str = None, age: int = None, gender: str = None):
        """Configure child settings"""
        if name:
            self.child_name = name
        if age:
            self.child_age = age
        if gender:
            self.child_gender = gender
        
        self.log_info(f"Çocuk ayarları: {self.child_name}, {self.child_age} yaş, {self.child_gender}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StorytellerPi Complete Setup")
    parser.add_argument("command", choices=[
        "install", "diagnostics", "setup-audio", "setup-python", 
        "setup-project", "setup-service", "help"
    ], help="Command to execute")
    parser.add_argument("--language", choices=["turkish", "english", "tr", "en"], 
                       default="turkish", help="Language setting")
    parser.add_argument("--child-name", help="Child name")
    parser.add_argument("--child-age", type=int, help="Child age")
    parser.add_argument("--child-gender", help="Child gender")
    parser.add_argument("--force", action="store_true", help="Force installation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create setup manager
    setup = StorytellerPiSetup()
    
    # Configure language
    setup.configure_language(args.language)
    
    # Configure child
    setup.configure_child(args.child_name, args.child_age, args.child_gender)
    
    # Execute command
    try:
        if args.command == "install":
            setup.install_complete()
        elif args.command == "diagnostics":
            setup.run_diagnostics()
        elif args.command == "setup-audio":
            setup.detect_hardware()
            setup.configure_audio_hardware()
        elif args.command == "setup-python":
            setup.create_python_environment()
            setup.install_python_dependencies()
        elif args.command == "setup-project":
            setup.setup_project_structure()
            setup.create_environment_file()
            setup.create_credentials_templates()
        elif args.command == "setup-service":
            setup.create_systemd_service()
        elif args.command == "help":
            parser.print_help()
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()