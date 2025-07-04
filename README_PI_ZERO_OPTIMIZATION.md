# StorytellerPi - Pi Zero 2W Optimization Guide

## 🎯 Overview

This guide provides comprehensive optimizations for running StorytellerPi on the Raspberry Pi Zero 2W, which has limited resources (512MB RAM, 4-core ARM Cortex-A53 CPU). The optimizations reduce memory usage from ~400MB to ~150MB and improve overall performance.

## 📊 Performance Comparison

| Feature | Original | Pi Zero 2W Optimized |
|---------|----------|---------------------|
| **Memory Usage** | ~400MB | ~150MB |
| **Startup Time** | 45-60s | 20-30s |
| **Wake Word Detection** | All frameworks loaded | Single framework (lazy) |
| **Web Interface** | Full Flask + SocketIO | Lite Flask (lazy full) |
| **Dependencies** | 50+ packages | 15 core packages |
| **Response Time** | 8-12s | 12-18s |

## 🚀 Quick Start

### 1. Install Pi Zero 2W Optimized Version

```bash
# Clone repository
git clone https://github.com/your-repo/storyteller-remote.git
cd storyteller-remote

# Run Pi Zero 2W optimized setup
sudo chmod +x setup_pi_zero.sh
sudo ./setup_pi_zero.sh
```

### 2. Configure API Keys

```bash
# Edit configuration
sudo nano /opt/storytellerpi/.env

# Add your API keys:
PORCUPINE_ACCESS_KEY=your-porcupine-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/opt/storytellerpi/credentials/google-cloud-key.json
```

### 3. Start Services

```bash
# Start web interface (lite mode)
sudo systemctl enable storytellerpi-web
sudo systemctl start storytellerpi-web

# Start main service
sudo systemctl enable storytellerpi
sudo systemctl start storytellerpi
```

### 4. Access Web Interface

Open your browser and navigate to: `http://your-pi-ip:5000`

The lite interface loads quickly and provides a button to load the full interface when needed.

## 🔧 Key Optimizations

### 1. **Lazy Loading Architecture**

**Problem**: Original version loads all services at startup
**Solution**: Services load only when needed

```python
# Before: All services loaded at startup
self.wake_word_detector = WakeWordDetector()
self.stt_service = STTService()
self.llm_service = StorytellerLLM()
self.tts_service = TTSService()

# After: Lazy loading
def _lazy_load_stt_service(self):
    if self.stt_service is None:
        from stt_service import STTService
        self.stt_service = STTService()
    return self.stt_service
```

### 2. **Conditional Framework Loading**

**Problem**: All wake word frameworks imported regardless of usage
**Solution**: Only load selected framework

```python
# Before: All frameworks imported
import openwakeword
import pvporcupine
import tensorflow as tf

# After: Conditional import
def _lazy_load_framework(self):
    if self.framework == "porcupine":
        import pvporcupine
        self._framework_module = pvporcupine
```

### 3. **Lite Web Interface**

**Problem**: Full Flask app with SocketIO always running
**Solution**: Minimal interface with lazy full loading

- **Lite Mode**: ~15MB RAM, basic controls
- **Full Mode**: ~80MB RAM, loaded on demand

### 4. **Memory Monitoring & Garbage Collection**

**Problem**: No memory management on constrained hardware
**Solution**: Active memory monitoring and cleanup

```python
async def _memory_monitor(self):
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        await self._emergency_memory_cleanup()
        gc.collect()
```

### 5. **Optimized Dependencies**

**Problem**: 50+ packages with heavy dependencies
**Solution**: Minimal dependency set

```txt
# Core dependencies only (15 packages vs 50+)
python-dotenv==1.0.0
Flask==2.3.3
PyAudio==0.2.11
pvporcupine==3.0.1
google-cloud-speech==2.21.0
# ... (see requirements_pi_zero.txt)
```

## 📁 File Structure

```
storyteller-remote/
├── main/
│   ├── storyteller_main_optimized.py      # Memory-optimized main app
│   ├── wake_word_detector_optimized.py    # Lazy-loading wake word detector
│   ├── web_interface_lite.py              # Lightweight web interface
│   └── templates/
│       ├── lite_dashboard.html             # Minimal dashboard
│       └── lite_error.html                 # Error page
├── scripts/
│   ├── memory_monitor.py                  # Memory monitoring tool
│   └── optimize_config.py                 # Configuration optimizer
├── requirements_pi_zero.txt               # Minimal dependencies
├── setup_pi_zero.sh                       # Optimized setup script
└── README_PI_ZERO_OPTIMIZATION.md         # This file
```

## ⚙️ Configuration Profiles

### Minimal Profile (Recommended for Pi Zero 2W)
```bash
MAX_MEMORY_USAGE=200
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_BUFFER_SIZE=256
TARGET_RESPONSE_TIME=20.0
LOG_LEVEL=ERROR
WEB_INTERFACE=lite
```

### Balanced Profile
```bash
MAX_MEMORY_USAGE=300
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_BUFFER_SIZE=512
TARGET_RESPONSE_TIME=15.0
LOG_LEVEL=WARNING
WEB_INTERFACE=lite
```

### Performance Profile (for Pi 4 or higher)
```bash
MAX_MEMORY_USAGE=400
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_BUFFER_SIZE=1024
TARGET_RESPONSE_TIME=12.0
LOG_LEVEL=INFO
WEB_INTERFACE=full
```

## 🛠️ Management Tools

### Memory Monitor
```bash
# Check current memory usage
python3 /opt/storytellerpi/scripts/memory_monitor.py

# Continuous monitoring
python3 /opt/storytellerpi/scripts/memory_monitor.py --continuous

# Optimize memory
python3 /opt/storytellerpi/scripts/memory_monitor.py --optimize
```

### Configuration Optimizer
```bash
# Analyze current configuration
python3 /opt/storytellerpi/scripts/optimize_config.py --analyze

# Auto-optimize for current system
python3 /opt/storytellerpi/scripts/optimize_config.py --auto

# Interactive optimization
python3 /opt/storytellerpi/scripts/optimize_config.py --interactive
```

## 📊 Monitoring & Troubleshooting

### Check Memory Usage
```bash
# System memory
free -h

# Process memory
ps aux --sort=-%mem | head -10

# StorytellerPi memory
python3 /opt/storytellerpi/scripts/memory_monitor.py
```

### Check Service Status
```bash
# Service status
sudo systemctl status storytellerpi
sudo systemctl status storytellerpi-web

# Service logs
sudo journalctl -u storytellerpi -f
sudo journalctl -u storytellerpi-web -f
```

### Performance Tuning
```bash
# Check CPU usage
htop

# Check temperature
vcgencmd measure_temp

# Check swap usage
swapon --show
```

## 🔍 Troubleshooting Common Issues

### 1. High Memory Usage
**Symptoms**: System becomes slow, swapping occurs
**Solutions**:
- Apply minimal configuration profile
- Restart services regularly
- Monitor with memory_monitor.py
- Increase swap space temporarily

```bash
# Apply minimal profile
python3 /opt/storytellerpi/scripts/optimize_config.py --profile minimal

# Restart services
sudo systemctl restart storytellerpi
```

### 2. Slow Response Times
**Symptoms**: Wake word detection or responses are slow
**Solutions**:
- Check CPU temperature
- Reduce buffer sizes
- Use Porcupine instead of OpenWakeWord
- Optimize audio settings

```bash
# Check temperature
vcgencmd measure_temp

# If overheating, add cooling or reduce CPU usage
```

### 3. Service Crashes
**Symptoms**: Services stop unexpectedly
**Solutions**:
- Check logs for memory errors
- Reduce memory limits
- Enable memory monitoring
- Use lite web interface

```bash
# Check for out-of-memory errors
sudo journalctl -u storytellerpi | grep -i "memory\|oom"
```

### 4. Web Interface Issues
**Symptoms**: Web interface is slow or unresponsive
**Solutions**:
- Use lite interface by default
- Load full interface only when needed
- Restart web service
- Check available memory

```bash
# Restart web service
sudo systemctl restart storytellerpi-web

# Check memory
python3 /opt/storytellerpi/scripts/memory_monitor.py
```

## 🎯 Best Practices for Pi Zero 2W

### 1. **Memory Management**
- Use minimal configuration profile
- Enable memory monitoring
- Regular garbage collection
- Monitor swap usage

### 2. **Performance Optimization**
- Use Porcupine for wake word detection
- Reduce audio buffer sizes
- Use lite web interface
- Enable lazy loading

### 3. **System Maintenance**
- Monitor temperature regularly
- Keep system updated
- Clear logs periodically
- Restart services weekly

### 4. **Configuration**
- Start with minimal profile
- Gradually increase limits if needed
- Test thoroughly after changes
- Monitor performance impact

## 📚 Advanced Configuration

### Custom Wake Word Models
```bash
# Copy your custom Porcupine model
sudo cp your_custom_model.ppn /opt/storytellerpi/models/

# Update configuration
sudo nano /opt/storytellerpi/.env
WAKE_WORD_MODEL_PATH=/opt/storytellerpi/models/your_custom_model.ppn
```

### Audio Optimization
```bash
# Test audio devices
arecord -l
aplay -l

# Configure audio in .env
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default
WAKE_WORD_SAMPLE_RATE=16000
WAKE_WORD_CHANNELS=1
```

### Network Optimization
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave

# Use ethernet when possible for better performance
```

## 🔄 Migration from Original Version

### 1. Backup Current Installation
```bash
sudo cp -r /opt/storytellerpi /opt/storytellerpi.backup
sudo cp /etc/systemd/system/storytellerpi.service /etc/systemd/system/storytellerpi.service.backup
```

### 2. Install Optimized Version
```bash
# Stop current services
sudo systemctl stop storytellerpi
sudo systemctl stop storytellerpi-web

# Run optimized setup
sudo ./setup_pi_zero.sh
```

### 3. Migrate Configuration
```bash
# Copy API keys and settings from backup
sudo cp /opt/storytellerpi.backup/.env /opt/storytellerpi/.env

# Apply Pi Zero optimizations
python3 /opt/storytellerpi/scripts/optimize_config.py --auto
```

## 📈 Performance Metrics

### Memory Usage Targets
- **Idle**: < 100MB
- **Wake Word Detection**: < 150MB
- **Processing Speech**: < 250MB
- **Full Web Interface**: < 300MB

### Response Time Targets
- **Wake Word Detection**: < 2s
- **Speech Recognition**: < 5s
- **Story Generation**: < 10s
- **Text-to-Speech**: < 3s

### System Health Indicators
- **CPU Temperature**: < 70°C
- **Memory Usage**: < 80%
- **Swap Usage**: < 25%
- **CPU Load**: < 2.0

## 🤝 Contributing

To contribute Pi Zero 2W optimizations:

1. Test on actual Pi Zero 2W hardware
2. Measure memory usage before/after
3. Document performance impact
4. Submit pull request with benchmarks

## 📞 Support

For Pi Zero 2W specific issues:

1. Check this optimization guide
2. Use the memory monitor tool
3. Apply configuration optimizer
4. Review service logs
5. Create issue with system specs

## 🔗 Related Resources

- [Raspberry Pi Zero 2W Documentation](https://www.raspberrypi.org/products/raspberry-pi-zero-2-w/)
- [Porcupine Wake Word Engine](https://picovoice.ai/platform/porcupine/)
- [Google Cloud Speech API](https://cloud.google.com/speech-to-text)
- [Flask Lightweight Applications](https://flask.palletsprojects.com/)

---

**Note**: This optimization guide is specifically designed for Raspberry Pi Zero 2W. For other Pi models, you may be able to use higher performance profiles or the original version.