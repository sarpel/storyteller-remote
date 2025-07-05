# StorytellerPi - Pi Zero 2W Optimized

Voice-activated storytelling device optimized for Raspberry Pi Zero 2W.

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd storyteller-remote

# Run complete setup (single script)
chmod +x setup_complete.sh
sudo ./setup_complete.sh
```

## Features

- ✅ Memory optimized for Pi Zero 2W (150MB RAM usage)
- ✅ USB audio auto-detection (Waveshare dongle support)  
- ✅ Lite web interface with lazy loading
- ✅ DietPi and Raspberry Pi OS compatible
- ✅ Automatic service management
- ✅ Built-in monitoring tools

## Hardware Setup

### Wake Word Button (Optional)
Connect a momentary push button for manual wake word activation:

```
GPIO Pin 18 (Physical Pin 12) → Button → Ground (Physical Pin 14)

Pi Zero 2W Pinout:
 1  3.3V    [ ][ ] 5V     2
 3  GPIO2   [ ][ ] 5V     4  
 5  GPIO3   [ ][ ] GND    6
 7  GPIO4   [ ][ ] GPIO14 8
 9  GND     [ ][ ] GPIO15 10
11  GPIO17  [●][ ] GPIO18 12  ← Connect button here
13  GPIO27  [ ][ ] GND    14  ← Connect to ground
```

### USB Audio Setup
- **Recommended**: Waveshare USB Audio Dongle
- **Auto-detection**: Plug into any USB port - automatically configured
- **Alternative**: Any USB audio device with microphone and speaker

## Post-Installation

1. Configure API keys in `/opt/storytellerpi/.env`
2. Copy wake word model to `/opt/storytellerpi/models/`
3. Connect hardware (button and USB audio)
4. Start services: `sudo systemctl start storytellerpi-web storytellerpi`
5. Access web interface: `http://your-pi-ip:5000`

## File Structure

```
storyteller-remote/
├── setup_complete.sh          # Single setup script (all-in-one)
├── main/                      # Application source code
│   ├── storyteller_main.py    # Main application
│   ├── web_interface.py       # Web interface
│   ├── wake_word_detector.py  # Wake word detection
│   ├── stt_service.py         # Speech-to-text
│   ├── storyteller_llm.py     # LLM integration
│   ├── tts_service.py         # Text-to-speech
│   ├── audio_feedback.py      # Audio feedback
│   └── templates/             # Web templates
├── models/                    # Wake word models
├── scripts/                   # Utility scripts
└── tests/                     # Test files
```

## System Requirements

- Raspberry Pi Zero 2W (512MB RAM)
- DietPi or Raspberry Pi OS
- USB audio dongle (optional)
- Internet connection for AI services

## Configuration

### API Keys Setup (Required)

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your API keys:**
   ```bash
   # Essential API keys (required)
   GEMINI_API_KEY=your-gemini-api-key           # Google Gemini for AI responses
   PORCUPINE_ACCESS_KEY=your-porcupine-key      # Picovoice Porcupine for wake word
   GOOGLE_CLOUD_PROJECT=your-project-id         # Google Cloud for STT/TTS
   
   # Optional API keys
   OPENAI_API_KEY=your-openai-key               # Alternative to Gemini
   ELEVENLABS_API_KEY=your-elevenlabs-key       # Premium TTS service
   
   # Hardware button settings
   WAKE_WORD_BUTTON_ENABLED=true
   WAKE_WORD_BUTTON_PIN=18
   
   # Audio settings
   USB_AUDIO_ENABLED=true
   AUDIO_SAMPLE_RATE=16000
   
   # Performance tuning
   MAX_MEMORY_USAGE=300
   LOG_LEVEL=WARNING
   ```

3. **Get your API keys:**
   - **Gemini API**: https://makersuite.google.com/app/apikey
   - **Porcupine**: https://console.picovoice.ai/
   - **Google Cloud**: https://console.cloud.google.com/apis/credentials
   - **OpenAI**: https://platform.openai.com/api-keys
   - **ElevenLabs**: https://elevenlabs.io/app/settings/api-keys

## Web Interface Features

Access at `http://your-pi-ip:5000` for:
- 📊 Real-time system monitoring (CPU, RAM, uptime)
- 🎛️ Service control (start/stop/restart)
- 🔧 Hardware status and pin diagram
- 📈 Performance metrics

## Service Management

```bash
# Check status
sudo systemctl status storytellerpi

# Control services
sudo systemctl start storytellerpi
sudo systemctl stop storytellerpi
sudo systemctl restart storytellerpi

# Enable/disable auto-start
sudo systemctl enable storytellerpi
sudo systemctl disable storytellerpi
```

## Support & Troubleshooting

- **Monitor memory**: `python3 /opt/storytellerpi/scripts/memory_monitor.py`
- **Check logs**: `sudo journalctl -u storytellerpi -f`
- **Test audio**: `sudo /opt/storytellerpi/scripts/test_audio.sh`
- **Audio issues**: Check USB audio auto-detection in web interface
- **Button not working**: Verify GPIO pin 18 connection
- **Service won't start**: Check API keys in `.env` file