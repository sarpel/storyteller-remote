#!/bin/bash
# Audio Diagnostics Script for Raspberry Pi Zero 2W
# Run this to diagnose audio issues

echo "🔍 Audio Diagnostics for Raspberry Pi Zero 2W"
echo "=============================================="

echo ""
echo "📋 System Information:"
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Hardware: $(cat /proc/cpuinfo | grep 'Model' | head -1 | cut -d':' -f2 | xargs)"

echo ""
echo "🔧 Hardware Detection:"
echo "--- I2C Devices ---"
sudo i2cdetect -y 1 2>/dev/null || echo "I2C not available or no devices found"

echo ""
echo "--- GPIO Status ---"
gpio readall 2>/dev/null || echo "gpio command not available"

echo ""
echo "📂 Boot Configuration:"
echo "--- /boot/config.txt Audio Settings ---"
grep -E "(dtparam=audio|dtoverlay.*audio|dtoverlay.*iqaudio|dtoverlay.*hifiberry)" /boot/config.txt || echo "No audio overlays found"

echo ""
echo "🎵 Audio System Status:"
echo "--- ALSA Cards ---"
cat /proc/asound/cards 2>/dev/null || echo "No ALSA cards found"

echo ""
echo "--- Audio Devices ---"
ls -la /dev/snd/ 2>/dev/null || echo "No /dev/snd/ directory found"

echo ""
echo "--- Playback Devices ---"
aplay -l 2>/dev/null || echo "No playback devices found"

echo ""
echo "--- Recording Devices ---"
arecord -l 2>/dev/null || echo "No recording devices found"

echo ""
echo "🔄 Loaded Modules:"
echo "--- Audio-related Modules ---"
lsmod | grep -E "(snd|audio|i2s|codec|wm8731|pcm512x)" || echo "No audio modules loaded"

echo ""
echo "📜 System Messages:"
echo "--- Recent Audio-related Kernel Messages ---"
dmesg | grep -i -E "(audio|sound|alsa|iqaudio|codec|i2s)" | tail -10 || echo "No audio-related messages"

echo ""
echo "⚙️  Audio Services:"
echo "--- ALSA Service Status ---"
systemctl status alsa-state 2>/dev/null || echo "ALSA service not found"

echo ""
echo "--- PulseAudio Status ---"
systemctl --user status pulseaudio 2>/dev/null || echo "PulseAudio not running"

echo ""
echo "📁 Configuration Files:"
echo "--- /etc/asound.conf ---"
if [ -f /etc/asound.conf ]; then
    cat /etc/asound.conf
else
    echo "No /etc/asound.conf file found"
fi

echo ""
echo "--- ~/.asoundrc ---"
if [ -f ~/.asoundrc ]; then
    cat ~/.asoundrc
else
    echo "No ~/.asoundrc file found"
fi

echo ""
echo "🔋 Power and Connectivity:"
echo "--- USB Devices ---"
lsusb 2>/dev/null || echo "lsusb not available"

echo ""
echo "--- Power Supply Info ---"
vcgencmd get_throttled 2>/dev/null || echo "vcgencmd not available"

echo ""
echo "💡 Troubleshooting Recommendations:"
echo "=================================="

# Check for common issues
if ! grep -q "dtoverlay=iqaudio" /boot/config.txt; then
    echo "❌ IQAudio overlay not found in /boot/config.txt"
    echo "   Add: dtoverlay=iqaudio-codec"
fi

if grep -q "dtparam=audio=on" /boot/config.txt; then
    echo "❌ Built-in audio is enabled - should be disabled"
    echo "   Change to: dtparam=audio=off"
fi

if ! groups $USER | grep -q audio; then
    echo "❌ User not in audio group"
    echo "   Run: sudo usermod -a -G audio $USER"
fi

if [ ! -d /dev/snd ]; then
    echo "❌ No /dev/snd directory - audio subsystem not initialized"
    echo "   Check kernel modules and reboot"
fi

echo ""
echo "🛠️  Next Steps:"
echo "1. If no audio devices found:"
echo "   - Check hardware connections"
echo "   - Verify HAT compatibility"
echo "   - Try alternative overlays"
echo ""
echo "2. If devices found but not working:"
echo "   - Run alsamixer to check levels"
echo "   - Test with: speaker-test -t sine -f 1000 -l 1 -s 1"
echo "   - Check /etc/asound.conf configuration"
echo ""
echo "3. Alternative HAT overlays to try:"
echo "   dtoverlay=iqaudio-dac"
echo "   dtoverlay=iqaudio-dacplus" 
echo "   dtoverlay=hifiberry-dac"
echo "   dtoverlay=i2s-gpio"

echo ""
echo "📞 If issues persist, report these details to support"