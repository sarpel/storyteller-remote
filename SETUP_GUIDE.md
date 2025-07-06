# StorytellerPi Setup Guide

Complete setup guide for StorytellerPi voice-activated storytelling device for Raspberry Pi Zero 2W.

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Keys Setup](#api-keys-setup)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Service Management](#service-management)

## 🔧 Hardware Requirements

### Required Hardware
- **Raspberry Pi Zero 2W** (minimum)
- **MicroSD Card** (32GB minimum, Class 10)
- **USB Audio Adapter** or I2S HAT
- **Microphone** (USB or connected to HAT)
- **Speaker** (3.5mm jack, USB, or Bluetooth)
- **MicroUSB Power Supply** (5V, 2.5A minimum)

### Optional Hardware
- **GPIO Button** (for manual wake word activation)
- **LED indicators** (for status display)
- **Case/Enclosure** (for protection)

## 💿 Software Requirements

### Operating System
- **Raspberry Pi OS Lite** (recommended)
- **DietPi** (alternative, lighter)
- **Ubuntu Server 22.04** (for Pi Zero 2W)

### Python Version
- **Python 3.9+** (required)

### System Dependencies
```bash
# Audio system
sudo apt update
sudo apt install -y alsa-utils pulseaudio pulseaudio-utils

# Python development
sudo apt install -y python3-pip python3-venv python3-dev

# Audio processing libraries
sudo apt install -y portaudio19-dev libportaudio2 libportaudiocpp0

# System monitoring
sudo apt install -y htop iotop

# Git (for installation)
sudo apt install -y git
```

## 🚀 Installation

### 1. Clone Repository
```bash
cd /opt
sudo git clone https://github.com/yourusername/storyteller-remote.git storytellerpi
sudo chown -R pi:pi storytellerpi
cd storytellerpi
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Directories
```bash
sudo mkdir -p /opt/storytellerpi/{logs,models,credentials,cache,temp,backups}
sudo chown -R pi:pi /opt/storytellerpi
```

## ⚙️ Configuration

### 1. Environment Variables Setup

Copy the example configuration and customize:
```bash
cp .env.example .env
nano .env
```

### 2. Required Environment Variables

#### **Core API Keys** (REQUIRED)
```bash
# Google Gemini AI (REQUIRED)
GEMINI_API_KEY=your-gemini-api-key-here

# Wake Word Detection Model Path (REQUIRED)
WAKE_WORD_MODEL_PATH=/opt/storytellerpi/models/hey_elsa.ppn
WAKE_WORD_FRAMEWORK=porcupine
```

#### **Audio Configuration**
```bash
# Audio Device Settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1024
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# Recording Settings
RECORDING_TIMEOUT=10.0
RECORDING_PHRASE_TIMEOUT=3.0
```

#### **Service Configuration**
```bash
# Speech-to-Text
STT_PRIMARY_SERVICE=google
STT_LANGUAGE_CODE=en-US
STT_TIMEOUT=30.0

# Language Model
LLM_SERVICE=gemini
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
LLM_CHILD_SAFE_MODE=true
LLM_AGE_APPROPRIATE_CONTENT=5

# Text-to-Speech
TTS_SERVICE=elevenlabs
TTS_VOICE_STABILITY=0.75
TTS_VOICE_SIMILARITY_BOOST=0.75
```

#### **System Settings**
```bash
# Installation Paths
INSTALL_DIR=/opt/storytellerpi
LOG_DIR=/opt/storytellerpi/logs
MODELS_DIR=/opt/storytellerpi/models

# Service Configuration
SERVICE_NAME=storytellerpi
LOG_LEVEL=INFO

# Performance
MAX_MEMORY_USAGE=400
TARGET_RESPONSE_TIME=11.0
```

### 3. Optional Environment Variables

#### **Advanced Audio Settings**
```bash
# Hardware-specific
AUDIO_HAT=iqaudio-codec
I2S_ENABLED=true
USB_AUDIO_ENABLED=true

# Audio Feedback
AUDIO_FEEDBACK_ENABLED=true
AUDIO_FEEDBACK_VOLUME=0.3
AUDIO_FEEDBACK_WAKE_WORD_TONE=880.0
AUDIO_FEEDBACK_WAKE_WORD_DURATION=0.3
```

#### **Web Interface**
```bash
# Web Interface Settings
WEB_ENABLED=true
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_SECRET_KEY=your-secret-key-here
WEB_DEBUG=false
```

#### **Performance Tuning**
```bash
# Memory Management
MEMORY_CHECK_INTERVAL=30.0
MEMORY_CLEANUP_THRESHOLD=350

# CPU Management
MAX_CPU_USAGE=80
CPU_CHECK_INTERVAL=10.0

# Health Monitoring
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=300.0
```

## 🔑 API Keys Setup

### 1. Google Gemini AI (REQUIRED)

1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Add to `.env`:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

### 2. Google Cloud Services (Optional - for STT)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Speech-to-Text API
4. Create service account and download JSON key
5. Place key file in `/opt/storytellerpi/credentials/`
6. Add to `.env`:
   ```bash
   GOOGLE_CREDENTIALS_JSON=/opt/storytellerpi/credentials/google-cloud-key.json
   GOOGLE_PROJECT_ID=your-project-id
   ```

### 3. ElevenLabs (Optional - for premium TTS)

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key from dashboard
3. Choose a voice ID from your library
4. Add to `.env`:
   ```bash
   ELEVENLABS_API_KEY=your-elevenlabs-api-key
   ELEVENLABS_VOICE_ID=your-voice-id
   ```

### 4. Porcupine Wake Word (Optional)

1. Sign up at [Picovoice Console](https://console.picovoice.ai/)
2. Get your access key
3. Download wake word model (.ppn file)
4. Add to `.env`:
   ```bash
   PORCUPINE_ACCESS_KEY=your-porcupine-access-key
   WAKE_WORD_MODEL_PATH=/opt/storytellerpi/models/hey_elsa.ppn
   ```

### 5. OpenAI (Optional - for STT fallback)

1. Get API key from [OpenAI](https://platform.openai.com/)
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=your-openai-api-key
   ```

## 🧪 Testing

### 1. Configuration Validation
```bash
cd /opt/storytellerpi
source venv/bin/activate
python main/config_validator.py
```

### 2. Service Tests
```bash
# Test all services
python main/service_manager.py

# Run unit tests
python -m pytest tests/test_basic.py -v

# Run integration tests
python -m pytest tests/test_integration.py -v
```

### 3. Audio System Test
```bash
# Test microphone
arecord -D hw:0,0 -f cd -t wav -d 5 test_recording.wav

# Test speaker
aplay test_recording.wav

# Test audio feedback
python -c "from main.audio_feedback import get_audio_feedback; get_audio_feedback().test_feedback()"
```

### 4. Individual Service Tests
```bash
# Test wake word detection
python -c "from main.wake_word_detector import WakeWordDetector; d = WakeWordDetector(); print('Wake word detector initialized')"

# Test TTS
python -c "import asyncio; from main.tts_service import TTSService; t = TTSService(); asyncio.run(t.test_voice())"

# Test LLM
python -c "import asyncio; from main.storyteller_llm import StorytellerLLM; l = StorytellerLLM(); print(asyncio.run(l.generate_response('Hello', 'conversation')))"
```

## 🔧 Service Management

### 1. Create Systemd Service
```bash
sudo nano /etc/systemd/system/storytellerpi.service
```

Add the following content:
```ini
[Unit]
Description=StorytellerPi Voice Assistant
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/storytellerpi
Environment=PATH=/opt/storytellerpi/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/storytellerpi/venv/bin/python main/storyteller_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=storytellerpi

# Resource limits for Pi Zero 2W
MemoryLimit=400M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable storytellerpi
sudo systemctl start storytellerpi
```

### 3. Service Management Commands
```bash
# Check status
sudo systemctl status storytellerpi

# View logs
sudo journalctl -u storytellerpi -f

# Restart service
sudo systemctl restart storytellerpi

# Stop service
sudo systemctl stop storytellerpi

# Disable service
sudo systemctl disable storytellerpi
```

### 4. Monitor System Health
```bash
# Run system monitor
python scripts/monitor.py --monitor

# Generate system report
python scripts/monitor.py --report

# Check system health
python scripts/monitor.py --check
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Audio Problems
```bash
# Check audio devices
aplay -l
arecord -l

# Test audio
speaker-test -t sine -f 1000 -l 1 -s 1

# Check ALSA configuration
cat /proc/asound/cards
```

#### 2. Permission Issues
```bash
# Add user to audio group
sudo usermod -a -G audio pi

# Fix file permissions
sudo chown -R pi:pi /opt/storytellerpi
sudo chmod +x /opt/storytellerpi/main/*.py
```

#### 3. Memory Issues
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Monitor in real-time
python scripts/monitor.py --monitor
```

#### 4. Service Startup Issues
```bash
# Check service logs
sudo journalctl -u storytellerpi -n 50

# Test manual startup
cd /opt/storytellerpi
source venv/bin/activate
python main/storyteller_main.py
```

#### 5. Network/API Issues
```bash
# Test internet connection
ping google.com

# Test API endpoints
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Check DNS
nslookup generativelanguage.googleapis.com
```

### Error Messages and Solutions

#### "Configuration validation failed"
- Check `.env` file exists and has required variables
- Verify API keys are valid
- Ensure file paths exist

#### "Audio device not found"
- Check `aplay -l` and `arecord -l` output
- Update `AUDIO_INPUT_DEVICE` and `AUDIO_OUTPUT_DEVICE`
- Try USB audio adapter

#### "Service failed to start"
- Check systemd logs: `sudo journalctl -u storytellerpi`
- Verify Python environment: `which python`
- Test manual startup for detailed errors

#### "Memory limit exceeded"
- Reduce `MAX_MEMORY_USAGE` in `.env`
- Enable swap if needed
- Consider DietPi for lower memory usage

### Performance Optimization

#### For Pi Zero 2W
```bash
# Set conservative performance settings
echo 'MAX_MEMORY_USAGE=300' >> .env
echo 'TARGET_RESPONSE_TIME=18.0' >> .env
echo 'LOG_LEVEL=WARNING' >> .env
echo 'ENABLE_MEMORY_MONITORING=true' >> .env
```

#### Audio Optimization
```bash
# Reduce audio buffer sizes
echo 'AUDIO_CHUNK_SIZE=512' >> .env
echo 'WAKE_WORD_BUFFER_SIZE=512' >> .env
```

## 📊 Monitoring and Maintenance

### 1. System Monitoring
```bash
# Start monitoring daemon
python scripts/monitor.py --monitor --interval 60

# View system status
python scripts/monitor.py --report
```

### 2. Log Management
```bash
# View application logs
tail -f /opt/storytellerpi/logs/storyteller.log

# View system logs
sudo journalctl -u storytellerpi -f

# Rotate logs (automatic with systemd)
sudo systemctl restart rsyslog
```

### 3. Health Checks
```bash
# Manual health check
python scripts/monitor.py --check

# Web interface health
curl http://localhost:8080/api/system/status
```

### 4. Backup Configuration
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

## 🔄 Updates and Maintenance

### Regular Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Clean up logs (if needed)
find logs/ -name "*.log" -mtime +7 -delete
```

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart storytellerpi
```

## 📞 Support

### Getting Help
- **Documentation**: This setup guide and README.md
- **Logs**: Check `/opt/storytellerpi/logs/` for detailed error information
- **System Status**: Use web interface at `http://pi-ip:8080`
- **Health Check**: Run `python scripts/monitor.py --check`

### Reporting Issues
When reporting issues, please include:
1. Raspberry Pi model and OS version
2. Error messages from logs
3. Configuration (with API keys redacted)
4. Steps to reproduce the issue

---

**Happy Storytelling! 🎭📚**