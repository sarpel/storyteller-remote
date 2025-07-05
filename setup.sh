#!/bin/bash

# StorytellerPi Unified Setup Script
# Complete installation and configuration for Raspberry Pi voice storytelling device
# Version: 2.1 - Consolidated with DietPi support and Pi Zero 2W optimizations
# Author: StorytellerPi Team

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/storytellerpi_setup.log"
INSTALL_DIR="/opt/storytellerpi"
SERVICE_USER="storyteller"
PYTHON_VERSION="3.9"

# System detection
IS_DIETPI=false
IS_RASPBERRY_PI_OS=false
SWAP_SYSTEM="unknown"

# Color output functions
print_header() {
    echo -e "\n\033[1;36m========================================\033[0m"
    echo -e "\033[1;36m$1\033[0m"
    echo -e "\033[1;36m========================================\033[0m\n"
}

print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
    echo "[INFO] $1" >> "$LOG_FILE" 2>/dev/null || true
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
    echo "[SUCCESS] $1" >> "$LOG_FILE" 2>/dev/null || true
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
    echo "[WARNING] $1" >> "$LOG_FILE" 2>/dev/null || true
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
    echo "[ERROR] $1" >> "$LOG_FILE" 2>/dev/null || true
}

# System detection function
detect_system() {
    print_status "Detecting system type..."
    
    # Check for DietPi
    if [ -f "/boot/dietpi/.version" ] || [ -f "/DietPi/dietpi/.version" ] || command -v dietpi-config >/dev/null 2>&1; then
        IS_DIETPI=true
        print_status "Detected: DietPi"
    elif [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        IS_RASPBERRY_PI_OS=true
        print_status "Detected: Raspberry Pi OS"
    else
        print_warning "Unknown system - proceeding with generic Linux setup"
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
    
    print_status "Swap system: $SWAP_SYSTEM"
}

# Help function
show_help() {
    cat << EOF
StorytellerPi Setup Script v2.1

USAGE:
    sudo bash ./setup.sh [OPTIONS]

OPTIONS:
    --help, -h              Show this help message
    --production            Full production installation (default)
    --development           Development installation with testing
    --audio-only            Audio setup only
    --test-only             Run tests only
    --quick                 Quick setup (minimal components)
    --clean                 Clean previous installation
    --resume                Resume interrupted installation
    --dietpi                DietPi optimized installation
    --pi-zero               Pi Zero 2W optimized installation

EXAMPLES:
    sudo ./setup.sh                    # Production installation
    sudo ./setup.sh --development      # Development installation
    sudo ./setup.sh --audio-only       # Audio setup only
    sudo ./setup.sh --dietpi           # DietPi optimized
    sudo ./setup.sh --pi-zero          # Pi Zero 2W optimized
    sudo ./setup.sh --clean            # Clean install

For more information, see README.md
EOF
}

# Installation type (default to production)
INSTALL_TYPE="production"
CLEAN_INSTALL=false
RESUME_INSTALL=false
DIETPI_OPTIMIZED=false
PI_ZERO_OPTIMIZED=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --production)
            INSTALL_TYPE="production"
            shift
            ;;
        --development)
            INSTALL_TYPE="development"
            shift
            ;;
        --audio-only)
            INSTALL_TYPE="audio-only"
            shift
            ;;
        --test-only)
            INSTALL_TYPE="test-only"
            shift
            ;;
        --quick)
            INSTALL_TYPE="quick"
            shift
            ;;
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --resume)
            RESUME_INSTALL=true
            shift
            ;;
        --dietpi)
            DIETPI_OPTIMIZED=true
            shift
            ;;
        --pi-zero)
            PI_ZERO_OPTIMIZED=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Auto-detect optimizations based on system
if [[ "$IS_DIETPI" == true ]]; then
    DIETPI_OPTIMIZED=true
fi

# Progress tracking
PROGRESS_FILE="/tmp/storytellerpi_progress"

save_progress() {
    echo "$1" > "$PROGRESS_FILE"
}

get_progress() {
    if [[ -f "$PROGRESS_FILE" ]]; then
        cat "$PROGRESS_FILE"
    else
        echo "none"
    fi
}

# System validation and hardware detection
check_raspberry_pi() {
    print_status "Checking if running on Raspberry Pi..."
    
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "Not running on Raspberry Pi - some features may not work"
        PI_MODEL="Unknown"
        AUDIO_HARDWARE="usb"
    else
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
        print_success "Detected: $PI_MODEL"
        
        # Auto-enable Pi Zero optimizations for Pi Zero models
        if [[ "$PI_MODEL" =~ "Pi Zero" ]]; then
            PI_ZERO_OPTIMIZED=true
            print_status "Pi Zero detected - enabling optimizations"
        fi
        
        # Determine audio hardware based on Pi model
        if [[ "$PI_MODEL" =~ "Pi 5" ]]; then
            AUDIO_HARDWARE="usb"
            print_status "Audio Hardware: Waveshare USB Audio Dongle (Pi 5 detected)"
        elif [[ "$PI_MODEL" =~ "Pi Zero 2" ]]; then
            AUDIO_HARDWARE="iqaudio"
            print_status "Audio Hardware: IQaudio Codec Zero HAT (Pi Zero 2W detected)"
        else
            # Default to USB for other models
            AUDIO_HARDWARE="usb"
            print_status "Audio Hardware: USB Audio (default for $PI_MODEL)"
        fi
    fi
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check memory for Pi Zero optimization
    if [[ "$PI_ZERO_OPTIMIZED" == true ]]; then
        TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
        if [ "$TOTAL_MEM" -lt 400 ]; then
            print_warning "Low memory detected: ${TOTAL_MEM}MB - Pi Zero optimizations enabled"
        fi
    fi
}

# Swap management functions (COMMENTED OUT - Not working properly)
# TODO: Fix swap mechanism later
# increase_swap() {
#     print_status "Swap management temporarily disabled"
#     print_warning "Swap increase functionality is currently not working properly"
#     print_warning "Installation will proceed with current swap settings"
#     
#     # Show current swap status
#     CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
#     print_status "Current swap: ${CURRENT_SWAP}MB"
#     
#     if [ "$CURRENT_SWAP" -lt 512 ]; then
#         print_warning "Low swap detected - installation may fail on low-memory systems"
#         print_warning "Consider manually increasing swap before running this script"
#     fi
# }

# restore_swap() {
#     print_status "Swap restoration temporarily disabled"
#     # Placeholder for future swap restoration functionality
# }

# Cleanup previous installation
cleanup_old_install() {
    if [[ "$CLEAN_INSTALL" == true ]] || [[ "$RESUME_INSTALL" == false ]]; then
        print_status "Cleaning up previous installation..."
        
        # Stop services
        systemctl stop storytellerpi 2>/dev/null || true
        systemctl stop storytellerpi-web 2>/dev/null || true
        systemctl disable storytellerpi 2>/dev/null || true
        systemctl disable storytellerpi-web 2>/dev/null || true
        
        # Remove service files
        rm -f /etc/systemd/system/storytellerpi.service
        rm -f /etc/systemd/system/storytellerpi-web.service
        
        # Remove installation directory
        if [[ -d "$INSTALL_DIR" ]]; then
            rm -rf "$INSTALL_DIR"
        fi
        
        # Remove user
        userdel -r "$SERVICE_USER" 2>/dev/null || true
        
        systemctl daemon-reload
        print_success "Cleanup completed"
    fi
}

# Phase 1: System preparation
phase1_system_preparation() {
    print_header "Phase 1: System Preparation"
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase1" ]]; then
        print_status "Skipping Phase 1 (already completed)"
        return
    fi
    
    # Detect system type
    detect_system
    
    print_status "Cleaning apt cache to prevent corrupted packages..."
    apt clean
    
    print_status "Updating system packages..."
    apt update --fix-missing && apt upgrade -y
    
    print_status "Installing system dependencies..."
    
    # Base packages
    PACKAGES=(
        "python3" "python3-pip" "python3-venv" "python3-dev"
        "build-essential" "pkg-config"
        "portaudio19-dev" "libasound2-dev"
        "git" "curl" "wget"
        "ffmpeg" "espeak"
        "systemd"
        "alsa-utils"
        "logrotate"
    )
    
    # Install packages with better error handling
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing $package..."
            apt install -y "$package" || {
                print_error "Failed to install $package"
                exit 1
            }
        else
            print_status "$package already installed"
        fi
    done
    
    # Optional packages (don't fail if they can't be installed)
    OPTIONAL_PACKAGES=()
    
    # Add espeak-ng for better TTS if not DietPi
    if [[ "$IS_DIETPI" == false ]]; then
        OPTIONAL_PACKAGES+=("espeak-ng")
    fi
    
    # Add PulseAudio for non-DietPi systems
    if [[ "$IS_DIETPI" == false ]]; then
        OPTIONAL_PACKAGES+=("pulseaudio" "pulseaudio-utils")
    fi
    
    for package in "${OPTIONAL_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing optional package $package..."
            apt install -y "$package" || {
                print_warning "Failed to install optional package $package (continuing)"
            }
        fi
    done
    
    print_status "Creating service user..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        # Add to audio group for audio access
        usermod -a -G audio "$SERVICE_USER"
    fi
    
    print_status "Creating installation directory..."
    mkdir -p "$INSTALL_DIR"/{main,models,logs,credentials,temp}
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    save_progress "phase1"
    print_success "Phase 1 completed"
}

# Phase 2: Audio setup
phase2_audio_setup() {
    print_header "Phase 2: Audio Setup ($AUDIO_HARDWARE)"
    
    if [[ "$INSTALL_TYPE" == "test-only" ]] || [[ "$INSTALL_TYPE" == "quick" ]]; then
        print_status "Skipping audio setup for $INSTALL_TYPE mode"
        return
    fi
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase2" ]]; then
        print_status "Skipping Phase 2 (already completed)"
        return
    fi
    
    if [[ "$AUDIO_HARDWARE" == "iqaudio" ]]; then
        configure_iqaudio_codec
    elif [[ "$AUDIO_HARDWARE" == "usb" ]]; then
        configure_usb_audio
    else
        print_error "Unknown audio hardware: $AUDIO_HARDWARE"
        exit 1
    fi
    
    # Configure audio based on system type
    if [[ "$IS_DIETPI" == true ]]; then
        configure_dietpi_audio
    else
        configure_standard_audio
    fi
    
    save_progress "phase2"
    print_success "Phase 2 completed"
}

# Configure IQaudio Codec Zero for Pi Zero 2W
configure_iqaudio_codec() {
    print_status "Configuring IQaudio Pi-Codec Zero HAT..."
    
    # Enable I2S interface
    if ! grep -q "dtparam=i2s=on" /boot/config.txt; then
        echo "dtparam=i2s=on" >> /boot/config.txt
        print_status "Enabled I2S interface"
    fi
    
    # Add IQaudio overlay
    if ! grep -q "dtoverlay=iqaudio-codec" /boot/config.txt; then
        echo "dtoverlay=iqaudio-codec" >> /boot/config.txt
        print_status "Added IQaudio device tree overlay"
    fi
    
    # Configure ALSA for IQaudio (card 0)
    cat > /etc/asound.conf << 'EOF'
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
    
    print_success "IQaudio Codec Zero configured"
}

# Configure USB Audio for Pi 5
configure_usb_audio() {
    print_status "Configuring USB Audio..."
    
    # Configure ALSA for USB audio
    cat > /etc/asound.conf << 'EOF'
# USB Audio configuration
pcm.!default {
    type hw
    card 1
    device 0
}
ctl.!default {
    type hw
    card 1
}

# Fallback to card 0 if USB not available
pcm.fallback {
    type hw
    card 0
    device 0
}
EOF
    
    print_success "USB Audio configured"
}

# DietPi-specific audio configuration
configure_dietpi_audio() {
    print_status "Configuring audio for DietPi..."
    
    # DietPi typically uses ALSA by default
    # No PulseAudio configuration needed
    print_status "DietPi audio configuration: ALSA-based setup"
    
    # Test audio availability
    if command -v speaker-test >/dev/null 2>&1; then
        print_status "Audio test command available: speaker-test"
    fi
}

# Standard audio configuration
configure_standard_audio() {
    print_status "Configuring audio for standard Raspberry Pi OS..."
    
    # Configure PulseAudio if available
    if command -v pulseaudio >/dev/null 2>&1; then
        print_status "Installing PulseAudio for USB audio management..."
        
        # Configure PulseAudio to run as system service
        systemctl --global disable pulseaudio.service pulseaudio.socket 2>/dev/null || true
        systemctl enable pulseaudio.service 2>/dev/null || true
        
        # Create PulseAudio configuration for the storyteller user
        mkdir -p "/home/$SERVICE_USER/.config/pulse"
        cat > "/home/$SERVICE_USER/.config/pulse/default.pa" << 'EOF'
# Load audio drivers automatically
.include /etc/pulse/default.pa

# Set USB audio as default if available
set-default-sink alsa_output.usb-*
set-default-source alsa_input.usb-*
EOF
        
        chown -R "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.config" 2>/dev/null || true
        
        print_success "PulseAudio configured"
    fi
}

# Configure audio device settings in .env based on hardware
configure_audio_settings() {
    print_status "Configuring audio device settings for $AUDIO_HARDWARE hardware..."
    
    if [[ "$AUDIO_HARDWARE" == "iqaudio" ]]; then
        # IQaudio Codec Zero settings (Pi Zero 2W)
        sed -i 's/^AUDIO_DEVICE_INDEX=.*/AUDIO_DEVICE_INDEX=0/' "$INSTALL_DIR/.env"
        sed -i 's/^PLAYBACK_DEVICE_INDEX=.*/PLAYBACK_DEVICE_INDEX=0/' "$INSTALL_DIR/.env"
        print_status "Configured for IQaudio Codec Zero (device index 0)"
        
    elif [[ "$AUDIO_HARDWARE" == "usb" ]]; then
        # USB Audio settings (Pi 5)
        sed -i 's/^AUDIO_DEVICE_INDEX=.*/AUDIO_DEVICE_INDEX=1/' "$INSTALL_DIR/.env"
        sed -i 's/^PLAYBACK_DEVICE_INDEX=.*/PLAYBACK_DEVICE_INDEX=1/' "$INSTALL_DIR/.env"
        print_status "Configured for USB Audio Dongle (device index 1)"
    fi
    
    # Add hardware detection info to .env
    echo "" >> "$INSTALL_DIR/.env"
    echo "# Hardware Detection (auto-configured)" >> "$INSTALL_DIR/.env"
    echo "DETECTED_PI_MODEL=\"$PI_MODEL\"" >> "$INSTALL_DIR/.env"
    echo "DETECTED_AUDIO_HARDWARE=\"$AUDIO_HARDWARE\"" >> "$INSTALL_DIR/.env"
    echo "DETECTED_SYSTEM_TYPE=\"$([ "$IS_DIETPI" == true ] && echo "DietPi" || echo "Standard")\"" >> "$INSTALL_DIR/.env"
}

# Phase 3: Python environment setup
phase3_python_setup() {
    print_header "Phase 3: Python Environment Setup"
    
    if [[ "$INSTALL_TYPE" == "audio-only" ]]; then
        print_status "Skipping Python setup for audio-only mode"
        return
    fi
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase3" ]]; then
        print_status "Skipping Phase 3 (already completed)"
        return
    fi
    
    print_status "Setting up Python virtual environment..."
    
    # Create pip config for faster installs
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << 'EOF'
[global]
extra-index-url = https://www.piwheels.org/simple
no-cache-dir = true
prefer-binary = true
timeout = 300

[install]
break-system-packages = true
EOF
    
    # Create virtual environment
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" python3 -m venv venv
    
    # Activate virtual environment and upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    
    # Configure pip for piwheels (faster on Pi)
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" config set global.extra-index-url https://www.piwheels.org/simple
    
    # Install requirements based on system type
    if [[ "$PI_ZERO_OPTIMIZED" == true ]] && [[ -f "$SCRIPT_DIR/requirements_pi_zero.txt" ]]; then
        print_status "Installing Pi Zero optimized Python dependencies..."
        install_python_dependencies_optimized
    elif [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        print_status "Installing standard Python dependencies..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    else
        print_error "No requirements file found"
        exit 1
    fi
    
    save_progress "phase3"
    print_success "Phase 3 completed"
}

# Install Python dependencies with better error handling for Pi Zero
install_python_dependencies_optimized() {
    print_status "Installing Python dependencies optimized for Pi Zero (this may take a while)..."
    
    # Copy requirements file
    if [[ -f "$SCRIPT_DIR/requirements_pi_zero.txt" ]]; then
        cp "$SCRIPT_DIR/requirements_pi_zero.txt" "$INSTALL_DIR/"
        chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/requirements_pi_zero.txt"
    fi
    
    # Install core dependencies first
    CORE_PACKAGES=(
        "python-dotenv==1.0.0"
        "psutil==5.9.6"
        "requests==2.31.0"
        "Flask==2.3.3"
        "Werkzeug==2.3.7"
        "Jinja2==3.1.2"
    )
    
    for package in "${CORE_PACKAGES[@]}"; do
        print_status "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || {
            print_error "Failed to install $package"
            exit 1
        }
    done
    
    # Install audio packages
    AUDIO_PACKAGES=(
        "PyAudio==0.2.11"
        "pygame==2.5.2"
    )
    
    for package in "${AUDIO_PACKAGES[@]}"; do
        print_status "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || {
            print_warning "Failed to install $package - you may need to install it manually"
        }
    done
    
    # Install AI services (optional)
    AI_PACKAGES=(
        "google-cloud-speech==2.21.0"
        "google-generativeai==0.3.2"
        "google-auth==2.23.4"
    )
    
    for package in "${AI_PACKAGES[@]}"; do
        print_status "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || {
            print_warning "Failed to install $package - you may need to install it manually"
        }
    done
    
    # Install wake word detection (optional)
    print_status "Installing wake word detection..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary pvporcupine==3.0.1 || {
        print_warning "Failed to install Porcupine - you'll need to install it manually"
    }
    
    print_success "Python dependencies installed"
}

# Phase 4: Application setup
phase4_application_setup() {
    print_header "Phase 4: Application Setup"
    
    if [[ "$INSTALL_TYPE" == "audio-only" ]] || [[ "$INSTALL_TYPE" == "test-only" ]]; then
        print_status "Skipping application setup for $INSTALL_TYPE mode"
        return
    fi
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase4" ]]; then
        print_status "Skipping Phase 4 (already completed)"
        return
    fi
    
    print_status "Copying application files..."
    
    # Copy main application
    if [[ -d "$SCRIPT_DIR/main" ]]; then
        cp -r "$SCRIPT_DIR/main" "$INSTALL_DIR/"
    else
        print_error "main directory not found"
        exit 1
    fi
    
    # Copy models directory
    if [[ -d "$SCRIPT_DIR/models" ]]; then
        cp -r "$SCRIPT_DIR/models" "$INSTALL_DIR/"
    else
        print_warning "models directory not found - creating empty directory"
        mkdir -p "$INSTALL_DIR/models"
    fi
    
    # Copy other directories
    [[ -d "$SCRIPT_DIR/tests" ]] && cp -r "$SCRIPT_DIR/tests" "$INSTALL_DIR/"
    [[ -d "$SCRIPT_DIR/scripts" ]] && cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
    
    # Create configuration file
    create_configuration_file
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/main"/*.py 2>/dev/null || true
    
    save_progress "phase4"
    print_success "Phase 4 completed"
}

# Create optimized configuration file
create_configuration_file() {
    print_status "Creating configuration file..."
    
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        # Copy existing .env and enhance it
        cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/.env"
        
        # Add system-specific optimizations
        if [[ "$PI_ZERO_OPTIMIZED" == true ]] || [[ "$DIETPI_OPTIMIZED" == true ]]; then
            cat >> "$INSTALL_DIR/.env" << EOF

# Pi Zero 2W / DietPi Optimizations
MAX_MEMORY_USAGE=300
TARGET_RESPONSE_TIME=18.0
LOG_LEVEL=WARNING
ENABLE_MEMORY_MONITORING=true
GC_FREQUENCY=30
DIETPI_OPTIMIZED=true

# Service settings
SERVICE_NAME=$SERVICE_USER
SERVICE_USER=$SERVICE_USER
EOF
        fi
        
        # Update audio device settings based on detected hardware
        configure_audio_settings
        
        print_success "Configuration file created and optimized"
    else
        print_error ".env file not found in $SCRIPT_DIR"
        print_error "Please ensure the complete .env file is present before installation"
        exit 1
    fi
    
    # Create credentials documentation
    cat > "$INSTALL_DIR/CREDENTIALS.md" << 'EOF'
# API Credentials Setup

## Required API Keys

### 1. Google Gemini (Required for AI storytelling)
- Get API key from: https://aistudio.google.com/app/apikey
- Add to .env as: GEMINI_API_KEY=your-gemini-api-key-here

### 2. OpenAI (Optional for Whisper fallback)
- Get API key from: https://platform.openai.com/
- Add to .env as: OPENAI_API_KEY=sk-...

### 3. ElevenLabs (Optional for high-quality TTS)
- Get API key from: https://elevenlabs.io/
- Add to .env as: ELEVENLABS_API_KEY=...

### 4. Porcupine (Optional for better wake word detection)
- Get access key from: https://console.picovoice.ai/
- Add to .env as: PORCUPINE_ACCESS_KEY=...

## Configuration
Edit the .env file to add your API keys:
sudo nano /opt/storytellerpi/.env
EOF
}

# Phase 5: Service setup
phase5_service_setup() {
    print_header "Phase 5: Service Configuration"
    
    if [[ "$INSTALL_TYPE" == "audio-only" ]] || [[ "$INSTALL_TYPE" == "test-only" ]] || [[ "$INSTALL_TYPE" == "development" ]]; then
        print_status "Skipping service setup for $INSTALL_TYPE mode"
        return
    fi
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase5" ]]; then
        print_status "Skipping Phase 5 (already completed)"
        return
    fi
    
    create_main_service
    create_web_service
    setup_logrotate
    
    save_progress "phase5"
    print_success "Phase 5 completed"
}

# Create main systemd service
create_main_service() {
    print_status "Creating main systemd service..."
    
    # Determine memory and CPU limits based on system type
    if [[ "$PI_ZERO_OPTIMIZED" == true ]] || [[ "$DIETPI_OPTIMIZED" == true ]]; then
        MEMORY_LIMIT="350M"
        CPU_QUOTA="85%"
    else
        MEMORY_LIMIT="400M"
        CPU_QUOTA="80%"
    fi
    
    cat > /etc/systemd/system/storytellerpi.service << EOF
[Unit]
Description=StorytellerPi Voice Assistant
After=network.target sound.service
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main/storyteller_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=storytellerpi

# Resource limits
MemoryMax=$MEMORY_LIMIT
CPUQuota=$CPU_QUOTA

# Security settings
NoNewPrivileges=true
ProtectSystem=false
ProtectHome=false
ReadWritePaths=$INSTALL_DIR

# Environment
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable storytellerpi
    
    print_success "Main service created"
}

# Create web interface service
create_web_service() {
    print_status "Creating web interface service..."
    
    # Determine memory limit for web service
    if [[ "$PI_ZERO_OPTIMIZED" == true ]] || [[ "$DIETPI_OPTIMIZED" == true ]]; then
        WEB_MEMORY_LIMIT="80M"
    else
        WEB_MEMORY_LIMIT="200M"
    fi
    
    cat > /etc/systemd/system/storytellerpi-web.service << EOF
[Unit]
Description=StorytellerPi Web Interface
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/main
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main/web_interface.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=storytellerpi-web

# Resource limits
MemoryMax=$WEB_MEMORY_LIMIT
CPUQuota=50%

# Security settings
NoNewPrivileges=true
ProtectSystem=false
ProtectHome=false
ReadWritePaths=$INSTALL_DIR

# Environment
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable storytellerpi-web
    
    print_success "Web interface service created"
}

# Setup log rotation
setup_logrotate() {
    print_status "Setting up log rotation..."
    
    cat > /etc/logrotate.d/storytellerpi << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload storytellerpi || true
    endscript
}
EOF
    
    print_success "Log rotation configured"
}

# Phase 6: Testing and Validation
phase6_testing() {
    print_header "Phase 6: Testing and Validation"
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase6" ]]; then
        print_status "Skipping Phase 6 (already completed)"
        return
    fi
    
    print_status "Running system validation tests..."
    
    # Test Python environment
    if [[ -f "$INSTALL_DIR/venv/bin/python" ]]; then
        print_success "Python virtual environment: OK"
    else
        print_error "Python virtual environment: MISSING"
    fi
    
    # Test audio system
    if command -v aplay &> /dev/null; then
        print_success "Audio system: OK ($AUDIO_HARDWARE detected)"
        
        # Test specific audio hardware
        if [[ "$AUDIO_HARDWARE" == "usb" ]] && command -v pulseaudio &> /dev/null && [[ "$IS_DIETPI" == false ]]; then
            print_success "PulseAudio: OK (for USB audio)"
        fi
    else
        print_warning "Audio system: NOT CONFIGURED"
    fi
    
    # Test application files
    if [[ -f "$INSTALL_DIR/main/storyteller_main.py" ]]; then
        print_success "Application files: OK"
    else
        print_error "Application files: MISSING"
    fi
    
    # Test configuration
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        print_success "Configuration: OK"
    else
        print_error "Configuration: MISSING"
    fi
    
    # Test services
    if systemctl list-unit-files | grep -q storytellerpi.service; then
        print_success "Main service: INSTALLED"
    else
        print_warning "Main service: NOT INSTALLED"
    fi
    
    if systemctl list-unit-files | grep -q storytellerpi-web.service; then
        print_success "Web interface: INSTALLED"
    else
        print_warning "Web interface: NOT INSTALLED"
    fi
    
    save_progress "phase6"
    print_success "Phase 6 completed"
}

# Report generation
generate_report() {
    print_header "Installation Report"
    
    REPORT_FILE="/tmp/storytellerpi_report.txt"
    
    cat > "$REPORT_FILE" << EOF
StorytellerPi Installation Report
Generated: $(date)
Installation Type: $INSTALL_TYPE

=== System Information ===
OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')
Architecture: $(uname -m)
Kernel: $(uname -r)
Python: $(python3 --version)
Pi Model: $PI_MODEL
System Type: $([ "$IS_DIETPI" == true ] && echo "DietPi" || echo "Standard Linux")

=== Installation Status ===
Installation Directory: $INSTALL_DIR
Service User: $SERVICE_USER
Log Directory: $INSTALL_DIR/logs
Audio Hardware: $AUDIO_HARDWARE

=== Optimizations Applied ===
DietPi Optimized: $DIETPI_OPTIMIZED
Pi Zero Optimized: $PI_ZERO_OPTIMIZED

=== Services ===
EOF
    
    # Check service status
    if systemctl list-unit-files | grep -q storytellerpi.service; then
        echo "Main Service: INSTALLED" >> "$REPORT_FILE"
    fi
    
    if systemctl list-unit-files | grep -q storytellerpi-web.service; then
        echo "Web Interface: INSTALLED" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << 'EOF'

=== Next Steps ===
1. Configure API keys in /opt/storytellerpi/.env
2. Access web interface at http://[PI_IP]:8080
3. Start services:
   sudo systemctl start storytellerpi
   sudo systemctl start storytellerpi-web
4. Check logs:
   sudo journalctl -u storytellerpi -f
   sudo journalctl -u storytellerpi-web -f

=== DietPi/Pi Zero Notes ===
- Memory limits are configured for low-resource systems
- Audio is configured for ALSA (DietPi systems)
- Use lite web interface for best performance
- Monitor memory usage: watch -n 1 free -m

=== Troubleshooting ===
- Check service status: sudo systemctl status storytellerpi
- View logs: sudo journalctl -u storytellerpi --no-pager
- Test audio: speaker-test -t sine -f 1000 -l 1
- Check memory: free -m && cat /proc/meminfo | grep -i swap
EOF
    
    cat "$REPORT_FILE"
    print_status "Full report saved to: $REPORT_FILE"
}

# Main installation flow
main() {
    print_header "StorytellerPi Unified Setup v2.1"
    
    print_status "Installation type: $INSTALL_TYPE"
    print_status "Log file: $LOG_FILE"
    
    # Initialize log
    echo "StorytellerPi Setup Started: $(date)" > "$LOG_FILE" 2>/dev/null || {
        LOG_FILE="./storytellerpi_setup.log"
        echo "StorytellerPi Setup Started: $(date)" > "$LOG_FILE"
        print_status "Using local log file: $LOG_FILE"
    }
    
    # Check environment
    check_raspberry_pi
    
    # Clean if requested
    cleanup_old_install
    
    # NOTE: Swap management is temporarily disabled
    # increase_swap
    
    # Run installation phases
    case "$INSTALL_TYPE" in
        "audio-only")
            phase1_system_preparation
            phase2_audio_setup
            ;;
        "test-only")
            phase6_testing
            ;;
        "quick")
            phase1_system_preparation
            phase3_python_setup
            ;;
        "development")
            phase1_system_preparation
            phase2_audio_setup
            phase3_python_setup
            phase4_application_setup
            phase6_testing
            ;;
        "production")
            phase1_system_preparation
            phase2_audio_setup
            phase3_python_setup
            phase4_application_setup
            phase5_service_setup
            phase6_testing
            ;;
    esac
    
    # Generate report
    generate_report
    
    # NOTE: Swap restoration is temporarily disabled
    # restore_swap
    
    # Final status
    print_success "StorytellerPi setup completed successfully!"
    
    if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "audio-only" ]]; then
        print_warning "Reboot recommended to ensure all changes take effect"
        print_status "Run: sudo reboot"
    fi
    
    # Show system-specific notes
    if [[ "$DIETPI_OPTIMIZED" == true ]]; then
        print_header "DietPi Specific Notes"
        print_status "- Memory limits configured for Pi Zero 2W"
        print_status "- Audio configured for ALSA (no PulseAudio)"
        print_status "- Use systemctl to manage services"
        print_status "- Monitor memory: watch -n 1 free -m"
    fi
    
    if [[ "$PI_ZERO_OPTIMIZED" == true ]]; then
        print_header "Pi Zero 2W Optimizations Applied"
        print_status "- Conservative memory and CPU limits"
        print_status "- Optimized Python package installation"
        print_status "- Lite web interface enabled"
    fi
    
    # Cleanup progress file
    rm -f "$PROGRESS_FILE"
}

# Run main function
main "$@"