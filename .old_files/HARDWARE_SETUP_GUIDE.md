# StorytellerPi Hardware-Specific Setup Guide

## 🎯 **Overview**

This guide covers the complete setup process for StorytellerPi with hardware-specific audio configuration for:

- **Pi Zero 2W** + **IQAudio Codec HAT**
- **Raspberry Pi 5** + **Waveshare USB Audio Dongle**
- **DietPi** and **Raspberry Pi OS** support

## 📋 **Supported Hardware Combinations**

### **Configuration Matrix**

| Hardware | OS | Audio Device | Configuration |
|----------|-----|--------------|---------------|
| Pi Zero 2W | DietPi | IQAudio Codec HAT | Optimized for low-power |
| Pi Zero 2W | Raspberry Pi OS | IQAudio Codec HAT | Full-featured |
| Raspberry Pi 5 | DietPi | Waveshare USB Audio | High-performance |
| Raspberry Pi 5 | Raspberry Pi OS | Waveshare USB Audio | Complete desktop |

## 🚀 **Quick Setup**

### **1. Download and Prepare**

```bash
# Clone the repository
git clone https://github.com/yourusername/storyteller-remote.git
cd storyteller-remote

# Make setup scripts executable
chmod +x setup_storyteller_pi.py
chmod +x setup_hardware_audio.py
```

### **2. Run Complete Setup**

```bash
# Run the complete setup (requires root)
sudo python3 setup_storyteller_pi.py
```

This single command will:
- ✅ Detect your hardware automatically
- ✅ Install all required packages
- ✅ Configure audio for your specific hardware
- ✅ Set up systemd services
- ✅ Create proper directory structure
- ✅ Configure environment variables

### **3. Reboot and Test**

```bash
# Reboot to apply all changes
sudo reboot

# After reboot, check services
sudo systemctl status storytellerpi
sudo systemctl status storytellerpi-web

# Test audio
speaker-test -t wav -c 2
```

---

## 🔧 **Manual Setup Options**

### **Hardware-Only Audio Setup**

If you only need audio configuration:

```bash
# Run just the hardware-specific audio setup
sudo python3 setup_hardware_audio.py
```

### **Web Interface Only**

If you only need the web interface:

```bash
# Fix and start web interface
python3 fix_web_interface.py
python3 start_web_interface.py
```

---

## 📦 **Hardware-Specific Configurations**

### **Pi Zero 2W + DietPi + IQAudio Codec HAT**

**Automatic Configuration:**
- ✅ Adds `dtoverlay=iqaudio-codec` to boot config
- ✅ Configures ALSA for hardware audio
- ✅ Sets up proper device permissions
- ✅ Installs minimal packages for DietPi

**Manual Verification:**
```bash
# Check if IQAudio HAT is detected
aplay -l | grep -i iqaudio

# Test audio output
speaker-test -D hw:0,0 -c 2 -t wav

# Test audio input
arecord -D hw:0,0 -f cd -t wav -d 5 test.wav
```

### **Pi Zero 2W + Raspberry Pi OS + IQAudio Codec HAT**

**Automatic Configuration:**
- ✅ Adds `dtoverlay=iqaudio-codec` to boot config
- ✅ Configures ALSA + PulseAudio integration
- ✅ Sets up user permissions
- ✅ Installs full audio stack

**Manual Verification:**
```bash
# Check PulseAudio configuration
pulseaudio --check -v

# Test via PulseAudio
paplay /usr/share/sounds/alsa/Front_Left.wav
```

### **Raspberry Pi 5 + DietPi + Waveshare USB Audio**

**Automatic Configuration:**
- ✅ Configures USB audio device detection
- ✅ Sets up ALSA for USB audio (card 1)
- ✅ Creates udev rules for device permissions
- ✅ Installs USB audio drivers

**Manual Verification:**
```bash
# Check USB audio device
lsusb | grep -i audio

# Test USB audio
speaker-test -D hw:1,0 -c 2 -t wav
```

### **Raspberry Pi 5 + Raspberry Pi OS + Waveshare USB Audio**

**Automatic Configuration:**
- ✅ Configures USB audio with PulseAudio
- ✅ Sets up automatic device switching
- ✅ Creates desktop audio integration
- ✅ Optimizes for full OS features

**Manual Verification:**
```bash
# Check PulseAudio USB audio
pactl list short sinks | grep -i usb

# Test via PulseAudio
paplay /usr/share/sounds/alsa/Front_Left.wav
```

---

## 🌐 **Web Interface Access**

After setup, the web interface will be available at:

- **Local:** http://localhost:5000
- **Network:** http://YOUR_PI_IP:5000

### **Web Interface Features**

- ✅ **Service Management** - Start/stop/restart services
- ✅ **System Monitoring** - CPU, memory, disk usage
- ✅ **Audio Testing** - Test speakers and microphone
- ✅ **Configuration** - Edit settings via web
- ✅ **Logs Viewing** - Real-time log monitoring

---

## 🛠 **Service Management**

### **Main StorytellerPi Service**

```bash
# Service control
sudo systemctl start storytellerpi
sudo systemctl stop storytellerpi
sudo systemctl restart storytellerpi
sudo systemctl status storytellerpi

# Enable/disable auto-start
sudo systemctl enable storytellerpi
sudo systemctl disable storytellerpi

# View logs
sudo journalctl -u storytellerpi -f
```

### **Web Interface Service**

```bash
# Service control
sudo systemctl start storytellerpi-web
sudo systemctl stop storytellerpi-web
sudo systemctl restart storytellerpi-web
sudo systemctl status storytellerpi-web

# View logs
sudo journalctl -u storytellerpi-web -f
```

---

## 🔍 **Troubleshooting**

### **Audio Issues**

**Problem:** No audio devices found
```bash
# Check hardware detection
sudo python3 setup_hardware_audio.py

# Verify audio devices
aplay -l
arecord -l

# Check ALSA configuration
cat /etc/asound.conf
```

**Problem:** Audio choppy or distorted
```bash
# Check audio settings in .env
cat /opt/storytellerpi/.env | grep AUDIO

# Test with different buffer sizes
export AUDIO_CHUNK_SIZE=2048
```

### **Service Issues**

**Problem:** Service won't start
```bash
# Check service logs
sudo journalctl -u storytellerpi --no-pager

# Check configuration
python3 -c "from main.config_validator import ConfigValidator; cv = ConfigValidator(); print(cv.load_and_validate())"

# Check permissions
ls -la /opt/storytellerpi/
```

**Problem:** Web interface not accessible
```bash
# Check web service
sudo systemctl status storytellerpi-web

# Check network binding
netstat -an | grep :5000

# Test locally
curl http://localhost:5000
```

### **Hardware Detection Issues**

**Problem:** Wrong hardware detected
```bash
# Check hardware info
cat /proc/cpuinfo | grep -i model
cat /proc/device-tree/model

# Check OS detection
cat /etc/os-release
ls -la /boot/
```

---

## 📝 **Configuration Files**

### **Key Files Created**

- **`/opt/storytellerpi/.env`** - Environment configuration
- **`/etc/asound.conf`** - ALSA audio configuration
- **`/boot/config.txt`** - Raspberry Pi hardware configuration
- **`/etc/systemd/system/storytellerpi.service`** - Main service
- **`/etc/systemd/system/storytellerpi-web.service`** - Web interface service

### **Environment Variables**

The setup creates hardware-specific environment variables:

```bash
# Hardware Detection
HARDWARE_MODEL=pi_zero_2w
OPERATING_SYSTEM=dietpi
AUDIO_DEVICE=iqaudio_codec_hat

# Audio Configuration
AUDIO_ENABLED=true
AUDIO_INPUT_DEVICE=hw:0,0
AUDIO_OUTPUT_DEVICE=hw:0,0
AUDIO_DRIVER=alsa
AUDIO_SYSTEM=alsa
AUDIO_DEVICE_NAME=IQAudio Codec HAT
```

---

## 🎉 **Success Verification**

### **Complete System Test**

```bash
# 1. Check hardware detection
sudo python3 setup_hardware_audio.py

# 2. Test audio output
speaker-test -t wav -c 2

# 3. Test audio input
arecord -f cd -t wav -d 3 test.wav && aplay test.wav

# 4. Check services
sudo systemctl status storytellerpi
sudo systemctl status storytellerpi-web

# 5. Test web interface
curl http://localhost:5000/api/system/status

# 6. Test StorytellerPi functionality
# (This requires API keys to be configured)
```

### **Expected Results**

✅ **Hardware detected correctly**  
✅ **Audio devices functional**  
✅ **Services running without errors**  
✅ **Web interface accessible**  
✅ **Configuration files created**  
✅ **Environment variables set**  

---

## 🔧 **Advanced Configuration**

### **Custom Audio Settings**

Edit `/opt/storytellerpi/.env`:

```bash
# Custom audio buffer settings
AUDIO_SAMPLE_RATE=44100
AUDIO_CHANNELS=2
AUDIO_CHUNK_SIZE=2048

# Custom device selection
AUDIO_INPUT_DEVICE=hw:1,0
AUDIO_OUTPUT_DEVICE=hw:1,0
```

### **Performance Tuning**

```bash
# Memory optimization
MAX_MEMORY_USAGE=200
ENABLE_MEMORY_MONITORING=true

# Response time optimization
TARGET_RESPONSE_TIME=8.0
AUDIO_CHUNK_SIZE=512
```

### **Development Mode**

```bash
# Enable debug mode
WEB_DEBUG=true
LOG_LEVEL=DEBUG

# Disable some services for testing
AUDIO_ENABLED=false
WAKE_WORD_ENABLED=false
```

---

## 🆘 **Getting Help**

If you encounter issues:

1. **Check the logs:**
   ```bash
   tail -f /opt/storytellerpi/logs/*.log
   sudo journalctl -u storytellerpi -f
   ```

2. **Run diagnostics:**
   ```bash
   python3 debug_web_interface.py
   ```

3. **Reset configuration:**
   ```bash
   sudo rm -rf /opt/storytellerpi
   sudo python3 setup_storyteller_pi.py
   ```

The hardware-specific setup system ensures your StorytellerPi works perfectly with your specific hardware configuration!