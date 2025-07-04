# 🎭 StorytellerPi

**Voice-activated storytelling device for children using Raspberry Pi Zero 2W**

A magical device that listens for "Hey Elsa" and tells personalized stories, answers questions, and engages in child-safe conversations using advanced AI services.

## 📋 What's New

✨ **Unified Installation**: All setup scripts consolidated into one simple `setup.sh` command!
✨ **Centralized Configuration**: Single `.env` file for all settings and API keys
✨ **Simplified Dependencies**: One `requirements.txt` file with all packages
✨ **Comprehensive Documentation**: Everything you need in one place

## 🎯 Features

- **Voice Activation**: "Hey Elsa" wake word detection
- **Child-Safe AI**: Stories and conversations appropriate for young children
- **Multi-Modal**: Stories, questions, conversations, and learning activities
- **Fast Response**: <11 second response time target
- **Offline Capable**: Local wake word detection, online AI services
- **Auto-Start**: Runs automatically on boot
- **Monitoring**: Health checks and performance monitoring
- **Audio Optimized**: High-quality audio with IQaudIO Pi-Codec Zero HAT
- **🔊 Audio Feedback**: Pleasant sounds for wake word detection and interactions
- **🌐 Web Interface**: Beautiful web-based configuration and management
- **📱 Mobile-Friendly**: Responsive design works on phones and tablets
- **🔧 No SSH Required**: Configure everything through the web interface

## 🛠️ Hardware Requirements

### Required Components
- **Raspberry Pi Zero 2W** (1GB RAM)
- **IQaudIO Pi-Codec Zero HAT** (audio interface)
- **32GB microSD card** (Class 10 or better)
- **Speakers or headphones** (connected to HAT)
- **Power supply** (5V 2.5A recommended)

### Optional Components
- **Microphone** (if not using HAT's built-in mic)
- **Case** (to protect the Pi and HAT)
- **LED indicators** (for status feedback)

## 🚀 Quick Start

### ⚡ One-Command Installation (5-8 minutes)

```bash
# Clone and install in one step
git clone https://github.com/yourusername/storyteller-remote.git
cd storyteller-remote
sudo ./setup.sh
```

### Installation Options

```bash
# Production setup (recommended)
sudo ./setup.sh --production

# Development setup with testing tools
sudo ./setup.sh --development

# Quick minimal install
sudo ./setup.sh --quick

# Audio hardware only
sudo ./setup.sh --audio-only

# Run tests only
sudo ./setup.sh --test-only

# Clean install (remove existing)
sudo ./setup.sh --clean

# Resume interrupted install
sudo ./setup.sh --resume

# Show all options
./setup.sh --help
```

> 💡 **Speed Boost**: Our unified installer uses pinned package versions and takes 5-8 minutes instead of 30+ minutes!

## ⚙️ Configuration

All configuration is done through a single `.env` file. Copy and customize:

```bash
# Copy the template
cp .env /opt/storytellerpi/.env

# Edit configuration
sudo nano /opt/storytellerpi/.env
```

### Essential Settings

```bash
# API Keys (Required)
GEMINI_API_KEY=your-gemini-api-key-here
GOOGLE_CREDENTIALS_JSON=/opt/storytellerpi/google-credentials.json
OPENAI_API_KEY=sk-your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Wake Word Settings
WAKE_WORD_MODEL_PATH=/opt/storytellerpi/models/hey_elsa.onnx
WAKE_WORD_THRESHOLD=0.5

# Child Safety
LLM_CHILD_SAFE_MODE=true
LLM_AGE_APPROPRIATE_CONTENT=5
```

### API Credentials Setup

1. **Google Gemini** (for AI storytelling):
   - Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Add to `.env` as `GEMINI_API_KEY=your-gemini-api-key-here`

2. **Google Cloud** (for Speech-to-Text):
   - Create project at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Speech-to-Text API
   - Create service account and download JSON key
   - Place at `/opt/storytellerpi/google-credentials.json`

3. **OpenAI** (for Whisper fallback):
   - Get API key from [OpenAI Platform](https://platform.openai.com/)
   - Add to `.env` as `OPENAI_API_KEY=sk-...`

4. **ElevenLabs** (for text-to-speech):
   - Get API key from [ElevenLabs](https://elevenlabs.io/)
   - Add to `.env` as `ELEVENLABS_API_KEY=...`

## 🌐 Web Interface

StorytellerPi includes a beautiful web interface for easy configuration and management - **no SSH or command line required!**

### Accessing the Web Interface

1. **From the Pi**: Open browser → `http://localhost:8080`
2. **From another device**: `http://[PI_IP_ADDRESS]:8080`
   - Find IP: `hostname -I`
   - Example: `http://192.168.1.100:8080`

### Features

#### 🎛️ **Dashboard**
- Real-time service status and system monitoring
- Start/stop/restart controls
- Quick audio and microphone tests
- System performance metrics (CPU, memory, temperature)
- Recent activity logs

#### ⚙️ **Settings Page**
- **API Configuration**: Secure management of all API keys
- **Wake Word Settings**: Choose engine, adjust sensitivity
- **Audio Settings**: Configure sample rate, volume, devices
- **AI Settings**: Set child's age, story length, creativity level
- **System Settings**: Performance limits, logging, memory

#### 🔧 **Easy Configuration**
- **Child-Friendly**: Simple controls for parents
- **Mobile-Responsive**: Works on phones and tablets
- **Real-Time Updates**: Live status monitoring
- **Secure**: API keys are masked and encrypted
- **Export/Import**: Backup and restore configurations

### Quick Setup via Web Interface

1. **Install StorytellerPi**: `sudo ./setup.sh`
2. **Open Web Interface**: `http://[PI_IP]:8080`
3. **Go to Settings**: Configure your API keys
4. **Set Child's Age**: Choose appropriate content level
5. **Test Audio**: Use dashboard test buttons
6. **Save & Restart**: Apply your configuration

> 💡 **The web interface is intuitive and self-explanatory - just open it in your browser!**

## 🎵 Audio Setup

### IQaudIO Pi-Codec Zero HAT Configuration

The setup script automatically configures the audio hardware:

```bash
# Audio-only setup
sudo ./setup.sh --audio-only
```

### Manual Audio Configuration

If you need to configure audio manually:

```bash
# Enable I2S interface
echo "dtparam=i2s=on" | sudo tee -a /boot/config.txt
echo "dtoverlay=iqaudio-codec" | sudo tee -a /boot/config.txt

# Configure ALSA
sudo tee /etc/asound.conf << EOF
pcm.!default {
    type hw
    card 0
    device 0
}
ctl.!default {
    type hw
    card 0
}
EOF

# Test audio
speaker-test -c 2 -t wav
```

### Audio Troubleshooting

```bash
# Check audio devices
aplay -l
arecord -l

# Test playback
aplay /usr/share/sounds/alsa/Front_Left.wav

# Test recording
arecord -D hw:0,0 -f cd test.wav
```

## 🔧 Usage

### Starting the Service

```bash
# Start service
sudo systemctl start storytellerpi

# Check status
sudo systemctl status storytellerpi

# View logs
sudo journalctl -u storytellerpi -f
```

### Manual Testing

```bash
# Development mode (with mock services)
cd /opt/storytellerpi
source venv/bin/activate
python storyteller_dev.py

# Production mode
python storyteller_main.py
```

### Voice Commands

1. **Wake up**: Say "Hey Elsa"
2. **Tell a story**: "Tell me a story about a brave princess"
3. **Ask questions**: "What do elephants eat?"
4. **Have conversations**: "How was your day?"
5. **Learning**: "Teach me about the solar system"

## 📊 Monitoring

### System Health

```bash
# Check system status
cd /opt/storytellerpi
python monitor.py --status

# Performance report
python monitor.py --performance

# Health check
python monitor.py --health
```

### Log Files

```bash
# Main application logs
tail -f /opt/storytellerpi/logs/storyteller.log

# Service logs
sudo journalctl -u storytellerpi -n 50

# System logs
tail -f /var/log/syslog | grep storyteller
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
cd /opt/storytellerpi
python -m pytest tests/

# Quick test suite
python run_tests.py --quick

# Integration tests
python run_tests.py --integration

# Performance tests
python run_tests.py --performance
```

### Manual Testing

```bash
# Test wake word detection
python -c "from main.wake_word_detector import WakeWordDetector; WakeWordDetector().test()"

# Test speech-to-text
python -c "from main.stt_service import STTService; STTService().test()"

# Test text-to-speech
python -c "from main.tts_service import TTSService; TTSService().test('Hello world')"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Audio Not Working
```bash
# Check audio hardware
lsmod | grep snd
cat /proc/asound/cards

# Reconfigure audio
sudo ./setup.sh --audio-only
sudo reboot
```

#### 2. Wake Word Not Detected
```bash
# Check microphone
arecord -D hw:0,0 -f cd test.wav
aplay test.wav

# Adjust sensitivity
# Edit WAKE_WORD_THRESHOLD in .env file
```

#### 3. API Errors
```bash
# Check credentials
ls -la /opt/storytellerpi/google-credentials.json

# Test API connectivity
python -c "import google.cloud.speech; print('Google Cloud: OK')"
python -c "import openai; print('OpenAI: OK')"
```

#### 4. Memory Issues
```bash
# Check memory usage
free -h
ps aux | grep storyteller

# Reduce memory usage in .env:
MAX_MEMORY_USAGE=300
LLM_MAX_TOKENS=500
```

#### 5. Service Won't Start
```bash
# Check service status
sudo systemctl status storytellerpi

# Check logs
sudo journalctl -u storytellerpi -n 50

# Restart service
sudo systemctl restart storytellerpi
```

### Performance Optimization

#### For Raspberry Pi Zero 2W
```bash
# In .env file:
MAX_MEMORY_USAGE=400
MAX_CPU_USAGE=80
TARGET_RESPONSE_TIME=11.0
LLM_MAX_TOKENS=800
```

#### For Raspberry Pi 4
```bash
# In .env file:
MAX_MEMORY_USAGE=1000
MAX_CPU_USAGE=90
TARGET_RESPONSE_TIME=8.0
LLM_MAX_TOKENS=1500
```

## 🔒 Security

### API Key Security
- Never commit API keys to version control
- Use environment variables only
- Set proper file permissions: `chmod 600 .env`
- Rotate API keys regularly

### Child Safety
- Content filtering enabled by default
- Age-appropriate responses (configurable)
- No data collection or storage
- Offline wake word detection

### Network Security
- HTTPS only for API calls
- Certificate validation enabled
- Network timeout protections
- No external access to device

## 📈 Performance

### Response Time Targets
- **Wake word detection**: <1 second
- **Speech-to-text**: <5 seconds
- **AI response generation**: <8 seconds
- **Text-to-speech**: <3 seconds
- **Total response time**: <11 seconds

### Resource Usage
- **Memory**: <400MB on Pi Zero 2W
- **CPU**: <80% average usage
- **Storage**: ~2GB for full installation
- **Network**: ~1MB per conversation

## 🔄 Updates and Maintenance

### Updating StorytellerPi
```bash
# Pull latest changes
cd storyteller-remote
git pull origin main

# Reinstall with updates
sudo ./setup.sh --clean --production
```

### Backup Configuration
```bash
# Backup .env file
cp /opt/storytellerpi/.env ~/storytellerpi-backup.env

# Backup credentials
cp /opt/storytellerpi/google-credentials.json ~/
```

### Log Rotation
Logs are automatically rotated daily with 7-day retention.

## 🚀 Advanced Features

### Custom Wake Words
1. Train your own wake word model
2. Place model file in `/opt/storytellerpi/models/`
3. Update `WAKE_WORD_MODEL_PATH` in `.env`

### Multi-Language Support
```bash
# In .env file:
STT_LANGUAGE_CODE=es-ES
LLM_LANGUAGE=spanish
TTS_VOICE_ID=spanish-voice-id
```

### Custom Voice Personalities
```bash
# In .env file:
LLM_TEMPERATURE=0.9
TTS_VOICE_STABILITY=0.8
LLM_PERSONALITY=playful_storyteller
```

## 🐛 Development

### Development Setup
```bash
# Install with development tools
sudo ./setup.sh --development

# Run in development mode
cd /opt/storytellerpi
source venv/bin/activate
python storyteller_dev.py
```

### Code Structure
```
storyteller-remote/
├── setup.sh                 # Unified installation script
├── .env                     # Central configuration
├── requirements.txt         # All dependencies
├── main/                    # Core application code
│   ├── storyteller_main.py  # Main application
│   ├── wake_word_detector.py # Wake word detection
│   ├── stt_service.py       # Speech-to-text
│   ├── storyteller_llm.py   # AI conversation
│   ├── tts_service.py       # Text-to-speech
│   └── monitor.py           # System monitoring
├── tests/                   # Test suite
├── models/                  # Wake word models
└── deprecated/              # Old scripts (reference)
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python run_tests.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenWakeWord** for wake word detection
- **Google Cloud** for speech services
- **ElevenLabs** for high-quality text-to-speech
- **Raspberry Pi Foundation** for amazing hardware
- **IQaudIO** for excellent audio HATs

## 📞 Support

### Getting Help
1. Check this README for common issues
2. Review logs: `sudo journalctl -u storytellerpi -n 50`
3. Run diagnostics: `python monitor.py --health`
4. Open an issue on GitHub

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and community support
- **Wiki**: Additional documentation and guides

---

**Made with ❤️ for children's imagination and learning**