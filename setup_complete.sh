#!/bin/bash

# =============================================================================
# STORYTELLER PI - MASTER SETUP SCRIPT
# Complete setup and management for StorytellerPi system
# Supports: Pi Zero 2W, Pi 5, DietPi, Raspberry Pi OS, Turkish/English
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
INSTALL_DIR="/opt/storytellerpi"
SERVICE_NAME="storytellerpi"
VENV_DIR="$INSTALL_DIR/venv"
USER_HOME="$HOME"
CURRENT_USER="$(whoami)"
SYSTEM_USER="storyteller"

# Hardware detection
PI_MODEL=""
PI_AUDIO_DEVICE=""
OS_TYPE=""
AUDIO_SETUP_TYPE=""

# Configuration
LANGUAGE="turkish"
SYSTEM_LANGUAGE="tr-TR"
CHILD_NAME="Küçük Prenses"
CHILD_AGE="5"
CHILD_GENDER="kız"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Bu script root olarak çalıştırılmamalı!"
        exit 1
    fi
}

check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_error "Sudo erişimi gerekli!"
        exit 1
    fi
}

# =============================================================================
# HARDWARE DETECTION
# =============================================================================

detect_pi_model() {
    log_info "Raspberry Pi modeli tespit ediliyor..."
    
    if [[ -f /proc/cpuinfo ]]; then
        local revision=$(grep "Revision" /proc/cpuinfo | awk '{print $3}')
        local model=$(grep "Model" /proc/cpuinfo | cut -d':' -f2 | xargs)
        
        if [[ "$model" == *"Zero 2"* ]]; then
            PI_MODEL="pi_zero_2w"
            PI_AUDIO_DEVICE="iqaudio_codec"
            log_success "Raspberry Pi Zero 2W tespit edildi"
        elif [[ "$model" == *"Pi 5"* ]]; then
            PI_MODEL="pi_5"
            PI_AUDIO_DEVICE="waveshare_usb"
            log_success "Raspberry Pi 5 tespit edildi"
        elif [[ "$model" == *"Pi 4"* ]]; then
            PI_MODEL="pi_4"
            PI_AUDIO_DEVICE="waveshare_usb"
            log_success "Raspberry Pi 4 tespit edildi"
        else
            PI_MODEL="unknown"
            PI_AUDIO_DEVICE="default"
            log_warn "Bilinmeyen Pi modeli: $model"
        fi
    else
        PI_MODEL="unknown"
        PI_AUDIO_DEVICE="default"
        log_warn "Pi modeli tespit edilemedi"
    fi
}

detect_os_type() {
    log_info "İşletim sistemi tespit ediliyor..."
    
    if [[ -f /etc/dietpi/dietpi-banner ]]; then
        OS_TYPE="dietpi"
        log_success "DietPi tespit edildi"
    elif [[ -f /etc/rpi-issue ]]; then
        OS_TYPE="raspios"
        log_success "Raspberry Pi OS tespit edildi"
    elif [[ -f /etc/debian_version ]]; then
        OS_TYPE="debian"
        log_success "Debian tabanlı sistem tespit edildi"
    else
        OS_TYPE="unknown"
        log_warn "Bilinmeyen işletim sistemi"
    fi
}

setup_audio_configuration() {
    log_info "Ses konfigürasyonu hazırlanıyor..."
    
    case "${PI_MODEL}_${OS_TYPE}" in
        "pi_zero_2w_dietpi")
            AUDIO_SETUP_TYPE="iqaudio_dietpi"
            ;;
        "pi_zero_2w_raspios")
            AUDIO_SETUP_TYPE="iqaudio_raspios"
            ;;
        "pi_5_dietpi")
            AUDIO_SETUP_TYPE="waveshare_dietpi"
            ;;
        "pi_5_raspios")
            AUDIO_SETUP_TYPE="waveshare_raspios"
            ;;
        *)
            AUDIO_SETUP_TYPE="default"
            ;;
    esac
    
    log_info "Ses konfigürasyonu: $AUDIO_SETUP_TYPE"
}

# =============================================================================
# SYSTEM SETUP
# =============================================================================

update_system() {
    log_info "Sistem güncellemeleri kontrol ediliyor..."
    
    sudo apt-get update -y
    sudo apt-get upgrade -y
    
    log_success "Sistem güncellendi"
}

install_system_packages() {
    log_info "Sistem paketleri yükleniyor..."
    
    # Base packages
    local packages=(
        "git"
        "curl"
        "wget"
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "build-essential"
        "pkg-config"
        "libffi-dev"
        "libssl-dev"
        "libjpeg-dev"
        "zlib1g-dev"
        "libtiff5-dev"
        "libopenjp2-7-dev"
        "libfreetype6-dev"
        "liblcms2-dev"
        "libwebp-dev"
        "libasound2-dev"
        "portaudio19-dev"
        "libsndfile1-dev"
        "systemd"
        "vim"
        "nano"
        "htop"
        "tree"
        "jq"
    )
    
    # OS-specific packages
    case "$OS_TYPE" in
        "dietpi")
            packages+=(
                "alsa-utils"
                "alsa-tools"
                "libasound2-plugins"
            )
            ;;
        "raspios")
            packages+=(
                "pulseaudio"
                "pulseaudio-utils"
                "alsa-utils"
                "alsa-tools"
                "libasound2-plugins"
            )
            ;;
    esac
    
    # Audio hardware specific packages
    case "$PI_AUDIO_DEVICE" in
        "iqaudio_codec")
            packages+=(
                "i2c-tools"
                "device-tree-compiler"
            )
            ;;
        "waveshare_usb")
            packages+=(
                "usb-modeswitch"
                "usb-modeswitch-data"
            )
            ;;
    esac
    
    # Install packages
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log_info "Yükleniyor: $package"
            sudo apt-get install -y "$package"
        fi
    done
    
    log_success "Sistem paketleri yüklendi"
}

# =============================================================================
# AUDIO SETUP
# =============================================================================

setup_audio_iqaudio_dietpi() {
    log_info "IQAudio Codec DietPi konfigürasyonu..."
    
    # Boot config
    sudo bash -c 'cat >> /boot/config.txt << EOF

# IQAudio Codec Zero HAT configuration
dtoverlay=iqaudio-codec
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
EOF'
    
    # ALSA configuration
    sudo bash -c 'cat > /etc/asound.conf << EOF
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
EOF'
    
    # Module loading
    sudo bash -c 'echo "snd_soc_iqaudio_codec" >> /etc/modules'
    
    log_success "IQAudio DietPi konfigürasyonu tamamlandı"
}

setup_audio_iqaudio_raspios() {
    log_info "IQAudio Codec Raspberry Pi OS konfigürasyonu..."
    
    # Boot config
    sudo bash -c 'cat >> /boot/config.txt << EOF

# IQAudio Codec Zero HAT configuration
dtoverlay=iqaudio-codec
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
EOF'
    
    # ALSA configuration
    sudo bash -c 'cat > /etc/asound.conf << EOF
pcm.!default {
    type pulse
    server unix:/run/user/$(id -u)/pulse/native
}

ctl.!default {
    type pulse
    server unix:/run/user/$(id -u)/pulse/native
}

pcm.hw_default {
    type hw
    card 0
    device 0
}

ctl.hw_default {
    type hw
    card 0
}
EOF'
    
    # PulseAudio configuration
    mkdir -p ~/.config/pulse
    cat > ~/.config/pulse/default.pa << EOF
#!/usr/bin/pulseaudio -nF
.include /etc/pulse/default.pa
set-default-sink alsa_output.hw_0_0
set-default-source alsa_input.hw_0_0
EOF
    
    log_success "IQAudio Raspberry Pi OS konfigürasyonu tamamlandı"
}

setup_audio_waveshare_dietpi() {
    log_info "Waveshare USB Audio DietPi konfigürasyonu..."
    
    # USB audio configuration
    sudo bash -c 'cat > /etc/asound.conf << EOF
pcm.!default {
    type hw
    card 1
    device 0
}

ctl.!default {
    type hw
    card 1
}
EOF'
    
    # USB audio module loading
    sudo bash -c 'echo "snd_usb_audio" >> /etc/modules'
    
    # USB rules
    sudo bash -c 'cat > /etc/udev/rules.d/99-usb-audio.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="controlC[0-9]*", ATTR{id}=="USB*", MODE="0666"
EOF'
    
    log_success "Waveshare USB DietPi konfigürasyonu tamamlandı"
}

setup_audio_waveshare_raspios() {
    log_info "Waveshare USB Audio Raspberry Pi OS konfigürasyonu..."
    
    # ALSA configuration
    sudo bash -c 'cat > /etc/asound.conf << EOF
pcm.!default {
    type pulse
    server unix:/run/user/$(id -u)/pulse/native
}

ctl.!default {
    type pulse
    server unix:/run/user/$(id -u)/pulse/native
}

pcm.hw_usb {
    type hw
    card 1
    device 0
}

ctl.hw_usb {
    type hw
    card 1
}
EOF'
    
    # PulseAudio configuration
    mkdir -p ~/.config/pulse
    cat > ~/.config/pulse/default.pa << EOF
#!/usr/bin/pulseaudio -nF
.include /etc/pulse/default.pa
set-default-sink alsa_output.usb-*
set-default-source alsa_input.usb-*
EOF
    
    # USB rules
    sudo bash -c 'cat > /etc/udev/rules.d/99-usb-audio.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="controlC[0-9]*", ATTR{id}=="USB*", MODE="0666"
EOF'
    
    log_success "Waveshare USB Raspberry Pi OS konfigürasyonu tamamlandı"
}

setup_audio_hardware() {
    log_info "Ses donanımı konfigürasyonu başlatılıyor..."
    
    case "$AUDIO_SETUP_TYPE" in
        "iqaudio_dietpi")
            setup_audio_iqaudio_dietpi
            ;;
        "iqaudio_raspios")
            setup_audio_iqaudio_raspios
            ;;
        "waveshare_dietpi")
            setup_audio_waveshare_dietpi
            ;;
        "waveshare_raspios")
            setup_audio_waveshare_raspios
            ;;
        *)
            log_warn "Varsayılan ses konfigürasyonu kullanılıyor"
            ;;
    esac
    
    # Test audio setup
    test_audio_setup
    
    log_success "Ses donanımı konfigürasyonu tamamlandı"
}

test_audio_setup() {
    log_info "Ses kurulumu test ediliyor..."
    
    # Test sound cards
    if aplay -l > /dev/null 2>&1; then
        log_success "Ses kartları tespit edildi"
        aplay -l
    else
        log_warn "Ses kartı tespit edilemedi"
    fi
    
    # Test ALSA
    if amixer > /dev/null 2>&1; then
        log_success "ALSA çalışıyor"
        amixer sset Master 80%
    else
        log_warn "ALSA problemi"
    fi
    
    # Test PulseAudio (if available)
    if command -v pulseaudio > /dev/null 2>&1; then
        if pulseaudio --check; then
            log_success "PulseAudio çalışıyor"
        else
            log_info "PulseAudio başlatılıyor..."
            pulseaudio --start --log-target=syslog
        fi
    fi
}

# =============================================================================
# PYTHON ENVIRONMENT SETUP
# =============================================================================

create_python_environment() {
    log_info "Python sanal ortamı oluşturuluyor..."
    
    # Create install directory
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Python sanal ortamı oluşturuldu"
}

install_python_dependencies() {
    log_info "Python bağımlılıkları yükleniyor..."
    
    source "$VENV_DIR/bin/activate"
    
    # Core dependencies
    pip install flask flask-socketio
    pip install pyaudio numpy scipy
    pip install pygame
    pip install requests aiohttp
    pip install python-dotenv
    pip install asyncio-mqtt
    pip install psutil
    
    # AI/ML dependencies
    pip install openai google-generativeai
    pip install google-cloud-speech
    pip install elevenlabs
    
    # Wake word detection
    pip install openwakeword
    
    # Audio processing
    pip install webrtcvad
    pip install librosa
    
    # System dependencies
    pip install systemd-python
    pip install dbus-python
    
    # Development dependencies
    pip install pytest pytest-asyncio
    pip install black flake8
    
    log_success "Python bağımlılıkları yüklendi"
}

# =============================================================================
# PROJECT SETUP
# =============================================================================

setup_project_structure() {
    log_info "Proje yapısı oluşturuluyor..."
    
    # Create directories
    mkdir -p "$INSTALL_DIR/main"
    mkdir -p "$INSTALL_DIR/models"
    mkdir -p "$INSTALL_DIR/credentials"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/tests"
    mkdir -p "$INSTALL_DIR/scripts"
    
    # Copy project files
    if [[ -d "$PROJECT_DIR/main" ]]; then
        cp -r "$PROJECT_DIR/main"/* "$INSTALL_DIR/main/"
    fi
    
    if [[ -d "$PROJECT_DIR/models" ]]; then
        cp -r "$PROJECT_DIR/models"/* "$INSTALL_DIR/models/"
    fi
    
    if [[ -d "$PROJECT_DIR/tests" ]]; then
        cp -r "$PROJECT_DIR/tests"/* "$INSTALL_DIR/tests/"
    fi
    
    if [[ -d "$PROJECT_DIR/scripts" ]]; then
        cp -r "$PROJECT_DIR/scripts"/* "$INSTALL_DIR/scripts/"
    fi
    
    # Copy requirements
    if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
        cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"
    fi
    
    # Set permissions
    chmod +x "$INSTALL_DIR/main"/*.py
    chmod +x "$INSTALL_DIR/scripts"/*.py
    
    log_success "Proje yapısı oluşturuldu"
}

create_environment_file() {
    log_info "Environment dosyası oluşturuluyor..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# StorytellerPi Configuration
PROJECT_NAME=StorytellerPi
PROJECT_VERSION=1.0.0
INSTALL_DIR=$INSTALL_DIR
LOG_DIR=$INSTALL_DIR/logs
MODELS_DIR=$INSTALL_DIR/models
CREDENTIALS_DIR=$INSTALL_DIR/credentials

# System Configuration
SYSTEM_LANGUAGE=$SYSTEM_LANGUAGE
STORY_LANGUAGE=$LANGUAGE
PI_MODEL=$PI_MODEL
PI_AUDIO_DEVICE=$PI_AUDIO_DEVICE
OS_TYPE=$OS_TYPE
AUDIO_SETUP_TYPE=$AUDIO_SETUP_TYPE

# Child Configuration
CHILD_NAME=$CHILD_NAME
CHILD_AGE=$CHILD_AGE
CHILD_GENDER=$CHILD_GENDER
STORY_TARGET_AUDIENCE=${CHILD_AGE}_year_old_${CHILD_GENDER}

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
STT_LANGUAGE_CODE=$SYSTEM_LANGUAGE
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
TTS_LANGUAGE=tr
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
STORY_THEMES=prenses,peri,dostluk,macera,hayvanlar
STORY_LENGTH=short
STORY_TONE=gentle_enthusiastic
STORY_INCLUDE_MORAL=true
STORY_AVOID_SCARY=true
STORY_CONTENT_FILTER=very_strict

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
GOOGLE_APPLICATION_CREDENTIALS=$INSTALL_DIR/credentials/google-credentials.json

# Service Management
SERVICE_AUTOSTART=true
SERVICE_RESTART_DELAY=5
SERVICE_MAX_RESTARTS=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=$INSTALL_DIR/logs/storyteller.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Security Configuration
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:*
ENABLE_AUTHENTICATION=false
EOF
    
    # Set permissions
    chmod 600 "$INSTALL_DIR/.env"
    
    log_success "Environment dosyası oluşturuldu"
}

create_credentials_templates() {
    log_info "Credentials şablonları oluşturuluyor..."
    
    # Google Cloud credentials template
    cat > "$INSTALL_DIR/credentials/google-credentials-template.json" << EOF
{
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
EOF
    
    # API keys template
    cat > "$INSTALL_DIR/credentials/api-keys-template.txt" << EOF
# StorytellerPi API Keys Configuration
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
EOF
    
    log_success "Credentials şablonları oluşturuldu"
}

# =============================================================================
# SYSTEMD SERVICE
# =============================================================================

create_systemd_service() {
    log_info "Systemd servisi oluşturuluyor..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=StorytellerPi - AI Storyteller for Children
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main/storyteller_main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# Environment
EnvironmentFile=$INSTALL_DIR/.env

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR
ReadOnlyPaths=/
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME.service
    
    log_success "Systemd servisi oluşturuldu"
}

# =============================================================================
# DIAGNOSTIC FUNCTIONS
# =============================================================================

run_diagnostics() {
    log_info "Sistem tanılaması başlatılıyor..."
    
    echo "=========================================="
    echo "StorytellerPi Sistem Tanılaması"
    echo "=========================================="
    
    # System information
    echo -e "\n${CYAN}Sistem Bilgileri:${NC}"
    echo "İşletim Sistemi: $OS_TYPE"
    echo "Pi Modeli: $PI_MODEL"
    echo "Ses Cihazı: $PI_AUDIO_DEVICE"
    echo "Ses Konfigürasyonu: $AUDIO_SETUP_TYPE"
    echo "Dil: $SYSTEM_LANGUAGE"
    
    # Hardware check
    echo -e "\n${CYAN}Donanım Kontrolü:${NC}"
    if [[ -f /proc/cpuinfo ]]; then
        echo "CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)"
        echo "Bellek: $(free -h | grep Mem | awk '{print $2}')"
    fi
    
    # Audio check
    echo -e "\n${CYAN}Ses Sistemi:${NC}"
    if command -v aplay > /dev/null 2>&1; then
        echo "ALSA: ✓ Mevcut"
        aplay -l 2>/dev/null | grep card || echo "Ses kartı bulunamadı"
    else
        echo "ALSA: ✗ Mevcut değil"
    fi
    
    if command -v pulseaudio > /dev/null 2>&1; then
        echo "PulseAudio: ✓ Mevcut"
        if pulseaudio --check; then
            echo "PulseAudio: ✓ Çalışıyor"
        else
            echo "PulseAudio: ✗ Çalışmıyor"
        fi
    else
        echo "PulseAudio: ✗ Mevcut değil"
    fi
    
    # Python environment
    echo -e "\n${CYAN}Python Ortamı:${NC}"
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        echo "Sanal ortam: ✓ Mevcut"
        source "$VENV_DIR/bin/activate"
        echo "Python: $(python --version)"
        echo "Pip: $(pip --version)"
    else
        echo "Sanal ortam: ✗ Mevcut değil"
    fi
    
    # Project files
    echo -e "\n${CYAN}Proje Dosyaları:${NC}"
    [[ -d "$INSTALL_DIR/main" ]] && echo "Ana dosyalar: ✓" || echo "Ana dosyalar: ✗"
    [[ -d "$INSTALL_DIR/models" ]] && echo "Modeller: ✓" || echo "Modeller: ✗"
    [[ -f "$INSTALL_DIR/.env" ]] && echo "Konfigürasyon: ✓" || echo "Konfigürasyon: ✗"
    
    # Services
    echo -e "\n${CYAN}Servisler:${NC}"
    if systemctl is-active $SERVICE_NAME.service > /dev/null 2>&1; then
        echo "StorytellerPi: ✓ Çalışıyor"
    else
        echo "StorytellerPi: ✗ Çalışmıyor"
    fi
    
    # Network
    echo -e "\n${CYAN}Ağ Bağlantısı:${NC}"
    if ping -c 1 google.com > /dev/null 2>&1; then
        echo "İnternet: ✓ Bağlı"
    else
        echo "İnternet: ✗ Bağlı değil"
    fi
    
    echo "=========================================="
    log_success "Sistem tanılaması tamamlandı"
}

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

show_help() {
    cat << EOF
StorytellerPi Master Setup Script

KULLANIM:
  $0 [KOMUT] [SEÇENEKLER]

KOMUTLAR:
  install       - Tam kurulum yap
  setup-audio   - Sadece ses kurulumu
  setup-python  - Sadece Python ortamı kurulumu
  setup-service - Sadece systemd servisi kurulumu
  start         - Servisi başlat
  stop          - Servisi durdur
  restart       - Servisi yeniden başlat
  status        - Servis durumunu göster
  logs          - Servis loglarını göster
  diagnostics   - Sistem tanılaması yap
  uninstall     - Kurulumu kaldır
  help          - Bu yardım metnini göster

SEÇENEKLER:
  --language [tr|en]     - Dil seçimi (varsayılan: tr)
  --child-name NAME      - Çocuk ismi
  --child-age AGE        - Çocuk yaşı
  --child-gender GENDER  - Çocuk cinsiyeti
  --force                - Zorla kurulum
  --debug                - Debug modu

ÖRNEKLER:
  $0 install
  $0 install --language tr --child-name "Zeynep" --child-age 5
  $0 setup-audio
  $0 diagnostics
  $0 start
  $0 logs

EOF
}

install_full() {
    log_info "StorytellerPi tam kurulumu başlatılıyor..."
    
    # Check prerequisites
    check_root
    check_sudo
    
    # Hardware detection
    detect_pi_model
    detect_os_type
    setup_audio_configuration
    
    # System setup
    update_system
    install_system_packages
    setup_audio_hardware
    
    # Python setup
    create_python_environment
    install_python_dependencies
    
    # Project setup
    setup_project_structure
    create_environment_file
    create_credentials_templates
    
    # Service setup
    create_systemd_service
    
    # Final steps
    log_success "StorytellerPi kurulumu tamamlandı!"
    log_info "Sıradaki adımlar:"
    log_info "1. API anahtarlarını yapılandırın: $INSTALL_DIR/credentials/"
    log_info "2. Konfigürasyonu kontrol edin: $INSTALL_DIR/.env"
    log_info "3. Sistemi yeniden başlatın: sudo reboot"
    log_info "4. Servisi başlatın: $0 start"
    log_info "5. Durumu kontrol edin: $0 status"
}

setup_audio_only() {
    log_info "Sadece ses kurulumu..."
    
    detect_pi_model
    detect_os_type
    setup_audio_configuration
    setup_audio_hardware
    
    log_success "Ses kurulumu tamamlandı"
}

setup_python_only() {
    log_info "Sadece Python ortamı kurulumu..."
    
    create_python_environment
    install_python_dependencies
    
    log_success "Python ortamı kurulumu tamamlandı"
}

setup_service_only() {
    log_info "Sadece systemd servisi kurulumu..."
    
    create_systemd_service
    
    log_success "Systemd servisi kurulumu tamamlandı"
}

start_service() {
    log_info "StorytellerPi servisi başlatılıyor..."
    
    sudo systemctl start $SERVICE_NAME.service
    
    if systemctl is-active $SERVICE_NAME.service > /dev/null; then
        log_success "Servis başarıyla başlatıldı"
    else
        log_error "Servis başlatılamadı"
        exit 1
    fi
}

stop_service() {
    log_info "StorytellerPi servisi durduruluyor..."
    
    sudo systemctl stop $SERVICE_NAME.service
    
    log_success "Servis durduruldu"
}

restart_service() {
    log_info "StorytellerPi servisi yeniden başlatılıyor..."
    
    sudo systemctl restart $SERVICE_NAME.service
    
    if systemctl is-active $SERVICE_NAME.service > /dev/null; then
        log_success "Servis yeniden başlatıldı"
    else
        log_error "Servis yeniden başlatılamadı"
        exit 1
    fi
}

show_service_status() {
    log_info "StorytellerPi servis durumu..."
    
    systemctl status $SERVICE_NAME.service
}

show_service_logs() {
    log_info "StorytellerPi servis logları..."
    
    journalctl -u $SERVICE_NAME.service -f
}

uninstall_service() {
    log_info "StorytellerPi kaldırılıyor..."
    
    # Stop and disable service
    sudo systemctl stop $SERVICE_NAME.service
    sudo systemctl disable $SERVICE_NAME.service
    sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
    sudo systemctl daemon-reload
    
    # Remove installation directory
    sudo rm -rf "$INSTALL_DIR"
    
    log_success "StorytellerPi kaldırıldı"
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

main() {
    local command="${1:-help}"
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --language)
                case $2 in
                    tr|turkish)
                        LANGUAGE="turkish"
                        SYSTEM_LANGUAGE="tr-TR"
                        ;;
                    en|english)
                        LANGUAGE="english"
                        SYSTEM_LANGUAGE="en-US"
                        ;;
                esac
                shift 2
                ;;
            --child-name)
                CHILD_NAME="$2"
                shift 2
                ;;
            --child-age)
                CHILD_AGE="$2"
                shift 2
                ;;
            --child-gender)
                CHILD_GENDER="$2"
                shift 2
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --debug)
                set -x
                shift
                ;;
            *)
                if [[ $1 != -* ]]; then
                    command="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Execute command
    case $command in
        install)
            install_full
            ;;
        setup-audio)
            setup_audio_only
            ;;
        setup-python)
            setup_python_only
            ;;
        setup-service)
            setup_service_only
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_service_status
            ;;
        logs)
            show_service_logs
            ;;
        diagnostics)
            run_diagnostics
            ;;
        uninstall)
            uninstall_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Bilinmeyen komut: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"