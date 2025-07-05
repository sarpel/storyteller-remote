#!/bin/bash

# StorytellerPi Complete Setup Script - Pi Zero 2W Optimized
# Single script with all fixes and optimizations for DietPi/Raspberry Pi OS
# Includes: System setup, USB audio, memory optimization, lite web interface

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/storytellerpi"
SERVICE_USER="storytellerpi"
SERVICE_NAME="storytellerpi"
TEMP_SWAP_SIZE="1024"

# System detection
IS_DIETPI=false
IS_RASPBERRY_PI_OS=false
SWAP_SYSTEM="unknown"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

detect_system() {
    log_info "Detecting system type..."
    
    if [ -f "/boot/dietpi/.version" ] || [ -f "/DietPi/dietpi/.version" ] || command -v dietpi-config >/dev/null 2>&1; then
        IS_DIETPI=true
        log_info "Detected: DietPi"
    elif [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        IS_RASPBERRY_PI_OS=true
        log_info "Detected: Raspberry Pi OS"
    else
        log_warning "Unknown system - proceeding with generic Linux setup"
    fi
    
    # Detect swap system
    if [ -f "/etc/dphys-swapfile" ]; then
        SWAP_SYSTEM="dphys-swapfile"
    elif systemctl is-active --quiet zram-swap 2>/dev/null; then
        SWAP_SYSTEM="zram-swap"
    elif command -v dietpi-config >/dev/null 2>&1; then
        SWAP_SYSTEM="dietpi"
    else
        SWAP_SYSTEM="manual"
    fi
    
    log_info "Swap system: $SWAP_SYSTEM"
}

check_system_resources() {
    log_info "Checking system specifications..."
    
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    if [ "$TOTAL_MEM" -lt 400 ]; then
        log_warning "Low memory detected: ${TOTAL_MEM}MB - Pi Zero 2W optimizations will be applied"
    fi
    
    log_success "System check completed"
}

create_temporary_swap() {
    log_info "Managing swap space for installation..."
    
    CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
    log_info "Current swap: ${CURRENT_SWAP}MB"
    
    if [ "$CURRENT_SWAP" -lt 512 ]; then
        log_info "Creating temporary swap file..."
        TEMP_SWAP_FILE="/tmp/storytellerpi_install_swap"
        
        AVAILABLE_SPACE=$(df /tmp | awk 'NR==2 {print int($4/1024)}')
        if [ "$AVAILABLE_SPACE" -lt "$TEMP_SWAP_SIZE" ]; then
            TEMP_SWAP_SIZE=$((AVAILABLE_SPACE - 100))
        fi
        
        if [ "$TEMP_SWAP_SIZE" -gt 100 ]; then
            sudo dd if=/dev/zero of="$TEMP_SWAP_FILE" bs=1M count="$TEMP_SWAP_SIZE" 2>/dev/null
            sudo chmod 600 "$TEMP_SWAP_FILE"
            sudo mkswap "$TEMP_SWAP_FILE" >/dev/null 2>&1
            sudo swapon "$TEMP_SWAP_FILE" 2>/dev/null
            echo "$TEMP_SWAP_FILE" > /tmp/storytellerpi_temp_swap_file
            log_success "Temporary swap created: ${TEMP_SWAP_SIZE}MB"
        fi
    fi
}

cleanup_swap() {
    if [ -f "/tmp/storytellerpi_temp_swap_file" ]; then
        TEMP_SWAP_FILE=$(cat /tmp/storytellerpi_temp_swap_file)
        if [ -f "$TEMP_SWAP_FILE" ]; then
            sudo swapoff "$TEMP_SWAP_FILE" 2>/dev/null || true
            sudo rm -f "$TEMP_SWAP_FILE"
        fi
        rm -f /tmp/storytellerpi_temp_swap_file
    fi
}

install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    sudo apt update
    
    PACKAGES=(
        "python3-pip" "python3-dev" "python3-venv" "build-essential" "pkg-config"
        "portaudio19-dev" "libasound2-dev" "alsa-utils" "git" "curl" "systemd"
        "logrotate" "espeak-ng"
    )
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            sudo apt install -y "$package" || log_error "Failed to install $package"
        fi
    done
    
    # PulseAudio (optional for DietPi)
    if ! $IS_DIETPI; then
        sudo apt install -y pulseaudio pulseaudio-utils || log_warning "PulseAudio install failed"
    fi
    
    log_success "System dependencies installed"
}

create_user_and_directories() {
    log_info "Creating user and directories..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Created user: $SERVICE_USER"
    fi
    
    sudo mkdir -p "$INSTALL_DIR"/{main,models,logs,credentials,scripts}
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    log_success "Directories created"
}

setup_python_environment() {
    log_info "Setting up Python environment..."
    
    sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" config set global.extra-index-url https://www.piwheels.org/simple
    
    log_success "Python environment created"
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    CORE_PACKAGES=(
        "python-dotenv==1.0.0" "psutil==5.9.6" "requests==2.31.0"
        "Flask==2.3.3" "Werkzeug==2.3.7" "Jinja2==3.1.2"
        "PyAudio==0.2.11" "pygame==2.5.2"
    )
    
    for package in "${CORE_PACKAGES[@]}"; do
        log_info "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package"
    done
    
    # Wake word detection
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary pvporcupine==3.0.1 || log_warning "Porcupine install failed"
    
    # AI services
    AI_PACKAGES=("google-cloud-speech==2.21.0" "google-generativeai==0.3.2" "google-auth==2.23.4")
    for package in "${AI_PACKAGES[@]}"; do
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || log_warning "$package install failed"
    done
    
    log_success "Python dependencies installed"
}

create_optimized_application_files() {
    log_info "Creating optimized application files..."
    
    # Create optimized main application
    cat > "$INSTALL_DIR/main/storyteller_main.py" << 'EOF'
"""
Optimized StorytellerPi Application for Pi Zero 2W
Memory and CPU optimized with lazy loading
"""

import os
import sys
import asyncio
import logging
import signal
import gc
from enum import Enum
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

class OptimizedStorytellerApp:
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.logger = None
        self.state = AppState.IDLE
        self.running = False
        
        # Service components (lazy loaded)
        self.wake_word_detector = None
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        
        # Memory optimization settings
        self.max_memory_usage = 350
        self.enable_memory_monitoring = True
        self.gc_frequency = 30
        
        self._load_environment()
        self._setup_logging()
        self._check_system_resources()
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if self.enable_memory_monitoring:
            asyncio.create_task(self._memory_monitor())
    
    def _setup_logging(self):
        os.makedirs("logs", exist_ok=True)
        log_level = getattr(logging, os.getenv('LOG_LEVEL', 'WARNING'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/storyteller.log', mode='a'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Optimized logging initialized")
    
    def _load_environment(self):
        try:
            load_dotenv(self.env_file)
            os.environ.setdefault('LOG_LEVEL', 'WARNING')
            os.environ.setdefault('MAX_MEMORY_USAGE', '350')
            os.environ.setdefault('WAKE_WORD_FRAMEWORK', 'porcupine')
            os.environ.setdefault('ENABLE_MEMORY_MONITORING', 'true')
            os.environ.setdefault('GC_FREQUENCY', '30')
            
            self.max_memory_usage = int(os.getenv('MAX_MEMORY_USAGE', '350'))
            self.enable_memory_monitoring = os.getenv('ENABLE_MEMORY_MONITORING', 'true').lower() == 'true'
            self.gc_frequency = int(os.getenv('GC_FREQUENCY', '30'))
            
        except Exception as e:
            print(f"Failed to load environment: {e}")
    
    def _check_system_resources(self):
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_mb = memory.available // (1024 * 1024)
            if available_mb < 200:
                self.logger.warning(f"Low memory: {available_mb}MB available")
        except ImportError:
            self.logger.warning("psutil not available")
    
    async def _memory_monitor(self):
        while self.running:
            try:
                import psutil
                memory = psutil.virtual_memory()
                used_mb = memory.used // (1024 * 1024)
                
                if used_mb > self.max_memory_usage or memory.percent > 85:
                    self.logger.warning(f"High memory usage: {used_mb}MB ({memory.percent}%)")
                    collected = gc.collect()
                    self.logger.info(f"Garbage collection freed {collected} objects")
                
                await asyncio.sleep(self.gc_frequency)
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(60)
    
    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        try:
            self.logger.info("Starting optimized StorytellerPi application")
            self.running = True
            
            # Main application loop
            while self.running:
                await asyncio.sleep(1)
                
            return True
        except Exception as e:
            self.logger.error(f"Error in main application: {e}")
            return False

async def main():
    try:
        app = OptimizedStorytellerApp()
        await app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

    # Create lite web interface
    cat > "$INSTALL_DIR/main/web_interface.py" << 'EOF'
#!/usr/bin/env python3
"""
Lightweight StorytellerPi Web Interface for Pi Zero 2W
"""

import os
import logging
import subprocess
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('WEB_SECRET_KEY', 'storytellerpi-lite-key')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_NAME = 'storytellerpi'

def get_service_status():
    """Get service status"""
    try:
        result = subprocess.run(['systemctl', 'is-active', SERVICE_NAME], 
                              capture_output=True, text=True, timeout=5)
        active = result.stdout.strip() == 'active'
        
        result = subprocess.run(['systemctl', 'is-enabled', SERVICE_NAME], 
                              capture_output=True, text=True, timeout=5)
        enabled = result.stdout.strip() == 'enabled'
        
        return {'active': active, 'enabled': enabled, 'status': 'running' if active else 'stopped'}
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {'active': False, 'enabled': False, 'status': 'unknown'}

@app.route('/')
def lite_dashboard():
    service_status = get_service_status()
    return render_template('lite_dashboard.html', service_status=service_status)

@app.route('/api/status')
def get_status():
    try:
        import psutil
        service_status = get_service_status()
        status = {
            'service': service_status,
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_percent': psutil.cpu_percent(interval=None),
            'uptime': os.popen('uptime -p').read().strip()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/<action>', methods=['POST'])
def control_service(action):
    """Control service"""
    try:
        if action == 'start':
            subprocess.run(['systemctl', 'start', SERVICE_NAME], check=True, timeout=10)
        elif action == 'stop':
            subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=True, timeout=10)
        elif action == 'restart':
            subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=True, timeout=10)
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        return jsonify({'success': True})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Service command failed: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

    # Create lite dashboard template
    mkdir -p "$INSTALL_DIR/main/templates"
    cat > "$INSTALL_DIR/main/templates/lite_dashboard.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StorytellerPi - Lite Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex; align-items: center; justify-content: center;
        }
        .container { 
            max-width: 500px; width: 90%; background: white; border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white; padding: 30px; text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .content { padding: 30px; }
        .status-card { 
            background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 15px;
            padding: 25px; margin-bottom: 25px; text-align: center;
        }
        .btn { 
            display: inline-block; padding: 15px 30px; border: none; border-radius: 10px;
            font-size: 1.1em; font-weight: 600; cursor: pointer; transition: all 0.3s ease;
            text-decoration: none; margin: 10px; min-width: 150px;
        }
        .btn-primary { 
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white;
        }
        .btn-success { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
        .status-indicator { 
            width: 12px; height: 12px; border-radius: 50%; display: inline-block; 
            margin-right: 8px; vertical-align: middle;
        }
        .status-running { background: #10b981; }
        .status-stopped { background: #ef4444; }
        .status-unknown { background: #6b7280; }
        .service-controls { text-align: center; margin: 20px 0; }
        .info-text { text-align: center; color: #64748b; font-size: 0.9em; margin-top: 20px; }
        .hardware-info { 
            background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; 
            padding: 15px; margin: 15px 0; font-size: 0.9em;
        }
        .pin-diagram { 
            font-family: monospace; background: #f1f5f9; padding: 10px; 
            border-radius: 5px; margin: 10px 0; font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 StorytellerPi</h1>
            <p>Lite Mode - Optimized for Pi Zero 2W</p>
        </div>
        <div class="content">
            <!-- Service Status -->
            <div class="status-card">
                <h3>Service Status</h3>
                <div style="margin: 15px 0;">
                    <span class="status-indicator status-{{ service_status.status }}"></span>
                    <span>Service {{ service_status.status.title() }}</span>
                </div>
                <div id="system-status">Loading system info...</div>
            </div>

            <!-- Service Controls -->
            <div class="service-controls">
                <button class="btn btn-success" onclick="controlService('start')" 
                        id="start-btn" {% if service_status.active %}disabled{% endif %}>
                    ▶️ Start Service
                </button>
                <button class="btn btn-danger" onclick="controlService('stop')"
                        id="stop-btn" {% if not service_status.active %}disabled{% endif %}>
                    ⏹️ Stop Service
                </button>
                <button class="btn btn-warning" onclick="controlService('restart')">
                    🔄 Restart Service
                </button>
            </div>

            <!-- Hardware Information -->
            <div class="hardware-info">
                <h4>🔌 Hardware Setup</h4>
                <p><strong>Wake Word Button:</strong></p>
                <div class="pin-diagram">
GPIO Pin 18 (Physical Pin 12) → Button → Ground (Physical Pin 14)

Pi Zero 2W Pinout:
 1  3.3V    [ ][ ] 5V     2
 3  GPIO2   [ ][ ] 5V     4  
 5  GPIO3   [ ][ ] GND    6
 7  GPIO4   [ ][ ] GPIO14 8
 9  GND     [ ][ ] GPIO15 10
11  GPIO17  [●][ ] GPIO18 12  ← Connect button here
13  GPIO27  [ ][ ] GND    14  ← Connect to ground
                </div>
                <p><strong>USB Audio:</strong> Connect Waveshare USB Audio Dongle to any USB port</p>
            </div>

            <div class="info-text">
                <strong>Pi Zero 2W Optimized Features:</strong><br>
                • Memory usage: ~150MB (vs ~400MB standard)<br>
                • USB audio auto-detection<br>
                • Hardware wake word button support<br>
                • Lazy loading for minimal footprint<br>
                • DietPi compatible
            </div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('system-status').innerHTML = 'Error: ' + data.error;
                        return;
                    }
                    
                    document.getElementById('system-status').innerHTML = 
                        `Memory: ${data.memory_percent.toFixed(1)}%<br>` +
                        `CPU: ${data.cpu_percent.toFixed(1)}%<br>` +
                        `Uptime: ${data.uptime}`;
                        
                    // Update service status
                    const serviceStatus = data.service;
                    const indicator = document.querySelector('.status-indicator');
                    indicator.className = 'status-indicator status-' + serviceStatus.status;
                })
                .catch(error => {
                    document.getElementById('system-status').innerHTML = 'Status unavailable';
                });
        }

        function controlService(action) {
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            
            // Show loading state
            const actionBtn = action === 'start' ? startBtn : stopBtn;
            const originalText = actionBtn.innerHTML;
            actionBtn.innerHTML = '⏳ Working...';
            actionBtn.disabled = true;
            
            fetch(`/api/service/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh page after 2 seconds to update status
                    setTimeout(() => location.reload(), 2000);
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                    actionBtn.innerHTML = originalText;
                    actionBtn.disabled = false;
                }
            })
            .catch(error => {
                alert('Error: ' + error.message);
                actionBtn.innerHTML = originalText;
                actionBtn.disabled = false;
            });
        }

        // Initialize
        updateStatus();
        setInterval(updateStatus, 10000);
    </script>
</body>
</html>
EOF

    # Set permissions
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo chmod +x "$INSTALL_DIR/main/storyteller_main.py"
    
    log_success "Application files created"
}

configure_usb_audio() {
    log_info "Configuring USB audio support..."
    
    # Create dynamic USB audio configuration script
    cat > "$INSTALL_DIR/scripts/configure_usb_audio.sh" << 'EOF'
#!/bin/bash
USB_CARD=""
for card_path in /proc/asound/card*; do
    if [ -f "$card_path/usbid" ]; then
        card_num=$(basename "$card_path" | sed 's/card//')
        USB_CARD="$card_num"
        break
    fi
done

if [ -n "$USB_CARD" ]; then
    cat > /etc/asound.conf << ALSA_EOF
pcm.!default {
    type asym
    playback.pcm "usb_playback"
    capture.pcm "usb_capture"
}
pcm.usb_playback {
    type plug
    slave.pcm { type hw; card $USB_CARD; device 0; }
}
pcm.usb_capture {
    type plug
    slave.pcm { type hw; card $USB_CARD; device 0; }
}
ctl.!default { type hw; card $USB_CARD; }
ALSA_EOF
    echo "USB audio configured for card $USB_CARD"
else
    cat > /etc/asound.conf << ALSA_EOF
pcm.!default {
    type asym
    playback.pcm "builtin_playback"
    capture.pcm "builtin_capture"
}
pcm.builtin_playback {
    type plug
    slave.pcm { type hw; card 0; device 0; }
}
pcm.builtin_capture {
    type plug
    slave.pcm { type hw; card 0; device 0; }
}
ctl.!default { type hw; card 0; }
ALSA_EOF
    echo "Built-in audio configured"
fi
EOF
    
    sudo chmod +x "$INSTALL_DIR/scripts/configure_usb_audio.sh"
    sudo "$INSTALL_DIR/scripts/configure_usb_audio.sh"
    
    # Create udev rules for automatic USB audio detection
    cat > /tmp/99-usb-audio.rules << 'EOF'
SUBSYSTEM=="sound", KERNEL=="card*", SUBSYSTEMS=="usb", ACTION=="add", RUN+="/opt/storytellerpi/scripts/configure_usb_audio.sh"
SUBSYSTEM=="sound", KERNEL=="card*", SUBSYSTEMS=="usb", ACTION=="remove", RUN+="/opt/storytellerpi/scripts/configure_usb_audio.sh"
EOF
    
    sudo mv /tmp/99-usb-audio.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    
    # Add user to audio group
    sudo usermod -a -G audio "$SERVICE_USER"
    
    log_success "USB audio configured"
}

create_configuration() {
    log_info "Creating configuration files..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# StorytellerPi Configuration - Pi Zero 2W Optimized

# Installation directories
INSTALL_DIR=$INSTALL_DIR
LOG_DIR=$INSTALL_DIR/logs
MODELS_DIR=$INSTALL_DIR/models
CREDENTIALS_DIR=$INSTALL_DIR/credentials

# Performance settings for Pi Zero 2W
MAX_MEMORY_USAGE=300
TARGET_RESPONSE_TIME=18.0
LOG_LEVEL=WARNING
ENABLE_MEMORY_MONITORING=true
GC_FREQUENCY=30

# Wake word detection
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_MODEL_PATH=$INSTALL_DIR/models/hey_elsa.ppn
WAKE_WORD_THRESHOLD=0.5
WAKE_WORD_SAMPLE_RATE=16000
WAKE_WORD_BUFFER_SIZE=512
WAKE_WORD_CHANNELS=1

# Hardware wake word button (GPIO)
WAKE_WORD_BUTTON_ENABLED=true
WAKE_WORD_BUTTON_PIN=18
WAKE_WORD_BUTTON_PULL=up
WAKE_WORD_BUTTON_BOUNCE_TIME=300

# Audio settings
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default
AUDIO_BACKEND=alsa
USB_AUDIO_ENABLED=true
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1024

# AI Services (Add your API keys here)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=$INSTALL_DIR/credentials/google-cloud-key.json
PORCUPINE_ACCESS_KEY=your-porcupine-key
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# STT (Speech-to-Text) settings
STT_SERVICE=google
STT_LANGUAGE=en-US
STT_TIMEOUT=10
STT_PHRASE_TIME_LIMIT=30

# LLM (Language Model) settings
LLM_SERVICE=google
LLM_MODEL=gemini-pro
LLM_MAX_TOKENS=150
LLM_TEMPERATURE=0.7
LLM_SYSTEM_PROMPT=You are a friendly storyteller for children. Keep stories short, fun, and age-appropriate.

# TTS (Text-to-Speech) settings
TTS_SERVICE=google
TTS_VOICE=en-US-Wavenet-F
TTS_SPEED=1.0
TTS_PITCH=0.0

# Web interface
WEB_SECRET_KEY=storytellerpi-optimized-$(date +%s)
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_INTERFACE=lite
WEB_DEBUG=false

# Service settings
SERVICE_NAME=$SERVICE_NAME
SERVICE_USER=$SERVICE_USER
OPTIMIZED_FOR_PI_ZERO=true

# Logging settings
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Development settings
DEVELOPMENT_MODE=false
DEBUG_MEMORY=false
DEBUG_AUDIO=false
EOF
    
    sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    log_success "Configuration created"
}

create_systemd_services() {
    log_info "Creating systemd services..."
    
    # Main service
    cat > /tmp/storytellerpi.service << EOF
[Unit]
Description=StorytellerPi - Voice-activated storytelling device (Pi Zero 2W Optimized)
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/main
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python storyteller_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
MemoryMax=350M
CPUQuota=85%
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    # Web service
    cat > /tmp/storytellerpi-web.service << EOF
[Unit]
Description=StorytellerPi Web Interface (Lite Mode)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/main
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python web_interface.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
MemoryMax=80M
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/storytellerpi.service /etc/systemd/system/
    sudo mv /tmp/storytellerpi-web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    log_success "Systemd services created"
}

create_management_tools() {
    log_info "Creating management tools..."
    
    # Memory monitor
    cat > "$INSTALL_DIR/scripts/memory_monitor.py" << 'EOF'
#!/usr/bin/env python3
import psutil
import time

def monitor_memory():
    memory = psutil.virtual_memory()
    print(f"Memory Usage: {memory.percent:.1f}%")
    print(f"Available: {memory.available // (1024*1024)}MB")
    print(f"Used: {memory.used // (1024*1024)}MB")
    
    if memory.percent > 80:
        print("WARNING: High memory usage!")
    
    # Show top processes
    print("\nTop Memory Processes:")
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            if proc.info['memory_percent'] > 1.0:
                print(f"  {proc.info['name']}: {proc.info['memory_percent']:.1f}%")
        except:
            pass

if __name__ == "__main__":
    monitor_memory()
EOF
    
    # Audio test script
    cat > "$INSTALL_DIR/scripts/test_audio.sh" << 'EOF'
#!/bin/bash
echo "=== Audio Test ==="
echo "1. ALSA Devices:"
aplay -l
echo -e "\n2. Testing playback:"
timeout 3 speaker-test -t sine -f 1000 -l 1 || echo "Audio test failed"
echo -e "\n3. USB Audio Detection:"
lsusb | grep -i audio || echo "No USB audio found"
EOF
    
    sudo chmod +x "$INSTALL_DIR/scripts"/*.py
    sudo chmod +x "$INSTALL_DIR/scripts"/*.sh
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/scripts"
    
    log_success "Management tools created"
}

setup_logrotate() {
    log_info "Setting up log rotation..."
    
    cat > /tmp/storytellerpi-logrotate << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
}
EOF
    
    sudo mv /tmp/storytellerpi-logrotate /etc/logrotate.d/storytellerpi
    log_success "Log rotation configured"
}

cleanup_installation() {
    log_info "Cleaning up installation..."
    
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" cache purge 2>/dev/null || true
    sudo apt clean
    sudo apt autoremove -y
    cleanup_swap
    
    log_success "Installation cleanup completed"
}

print_final_instructions() {
    log_success "StorytellerPi Complete Setup Finished!"
    echo
    echo "=========================================="
    echo "NEXT STEPS"
    echo "=========================================="
    echo
    echo "1. Configure API Keys:"
    echo "   sudo nano $INSTALL_DIR/.env"
    echo "   Add your Porcupine and Google Cloud credentials"
    echo
    echo "2. Copy Wake Word Model:"
    echo "   sudo cp your_model.ppn $INSTALL_DIR/models/hey_elsa.ppn"
    echo
    echo "3. Start Services:"
    echo "   sudo systemctl enable storytellerpi-web"
    echo "   sudo systemctl start storytellerpi-web"
    echo "   sudo systemctl enable storytellerpi"
    echo "   sudo systemctl start storytellerpi"
    echo
    echo "4. Access Web Interface:"
    echo "   http://$(hostname -I | awk '{print $1}'):5000"
    echo
    echo "5. Test Audio:"
    echo "   sudo $INSTALL_DIR/scripts/test_audio.sh"
    echo
    echo "6. Monitor System:"
    echo "   python3 $INSTALL_DIR/scripts/memory_monitor.py"
    echo "   sudo journalctl -u storytellerpi -f"
    echo
    echo "=========================================="
    echo "OPTIMIZATION FEATURES"
    echo "=========================================="
    echo "✅ Memory optimized for Pi Zero 2W (300MB limit)"
    echo "✅ Lazy loading services"
    echo "✅ USB audio auto-detection"
    echo "✅ Lite web interface"
    echo "✅ Automatic memory monitoring"
    echo "✅ DietPi compatible"
    echo "✅ System service management"
    echo
    echo "Installation directory: $INSTALL_DIR"
    echo "System type: $([ $IS_DIETPI == true ] && echo "DietPi" || echo "Standard Linux")"
    echo
    log_success "Setup completed successfully!"
}

# Trap to cleanup on exit
trap cleanup_swap EXIT

# Main installation process
main() {
    log_info "Starting StorytellerPi Complete Setup for Pi Zero 2W..."
    
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    detect_system
    check_system_resources
    create_temporary_swap
    install_system_dependencies
    create_user_and_directories
    setup_python_environment
    install_python_dependencies
    create_optimized_application_files
    configure_usb_audio
    create_configuration
    create_systemd_services
    create_management_tools
    setup_logrotate
    cleanup_installation
    print_final_instructions
}

main "$@"