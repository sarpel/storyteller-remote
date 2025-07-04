#!/bin/bash

# StorytellerPi Setup Script - Optimized for Pi Zero 2W with DietPi Support
# This script installs and configures StorytellerPi with minimal resource usage
# Supports both DietPi and standard Raspberry Pi OS

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
PYTHON_VERSION="3.11"
TEMP_SWAP_SIZE="1024"  # MB - Temporary increase for installation

# System detection
IS_DIETPI=false
IS_RASPBERRY_PI_OS=false
SWAP_SYSTEM="unknown"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_system() {
    log_info "Detecting system type..."
    
    # Check for DietPi
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

check_pi_zero() {
    log_info "Checking system specifications..."
    
    # Check if it's a Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null && ! $IS_DIETPI; then
        log_warning "This script is optimized for Raspberry Pi Zero 2W"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check memory
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    if [ "$TOTAL_MEM" -lt 400 ]; then
        log_warning "Low memory detected: ${TOTAL_MEM}MB"
        log_warning "Pi Zero 2W optimizations will be applied"
    fi
    
    log_success "System check completed"
}

increase_swap_dietpi() {
    log_info "Managing swap space for DietPi..."
    
    # Check current swap
    CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
    log_info "Current swap: ${CURRENT_SWAP}MB"
    
    if [ "$CURRENT_SWAP" -lt 512 ]; then
        log_info "Increasing swap space for installation..."
        
        # Try DietPi-specific methods first
        if command -v dietpi-config >/dev/null 2>&1; then
            log_info "Using DietPi configuration tools..."
            # Note: dietpi-config swap management would need to be done interactively
            # For now, we'll use manual method
            create_temporary_swap
        else
            create_temporary_swap
        fi
    else
        log_info "Sufficient swap space available"
    fi
}

increase_swap_standard() {
    log_info "Managing swap space for standard Raspberry Pi OS..."
    
    if [ "$SWAP_SYSTEM" = "dphys-swapfile" ]; then
        # Stop swap
        sudo dphys-swapfile swapoff 2>/dev/null || true
        
        # Backup original swapfile config
        sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.backup 2>/dev/null || true
        
        # Set new swap size
        sudo sed -i "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=${TEMP_SWAP_SIZE}/" /etc/dphys-swapfile
        
        # Setup and start new swap
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        
        log_success "Swap increased to ${TEMP_SWAP_SIZE}MB using dphys-swapfile"
    else
        create_temporary_swap
    fi
}

create_temporary_swap() {
    log_info "Creating temporary swap file..."
    
    # Create temporary swap file
    TEMP_SWAP_FILE="/tmp/storytellerpi_install_swap"
    
    # Check available space
    AVAILABLE_SPACE=$(df /tmp | awk 'NR==2 {print int($4/1024)}')
    if [ "$AVAILABLE_SPACE" -lt "$TEMP_SWAP_SIZE" ]; then
        log_warning "Insufficient space for temporary swap, using smaller size"
        TEMP_SWAP_SIZE=$((AVAILABLE_SPACE - 100))
    fi
    
    if [ "$TEMP_SWAP_SIZE" -gt 100 ]; then
        # Create and activate swap file
        sudo dd if=/dev/zero of="$TEMP_SWAP_FILE" bs=1M count="$TEMP_SWAP_SIZE" 2>/dev/null || {
            log_warning "Failed to create temporary swap file"
            return 1
        }
        
        sudo chmod 600 "$TEMP_SWAP_FILE"
        sudo mkswap "$TEMP_SWAP_FILE" >/dev/null 2>&1
        sudo swapon "$TEMP_SWAP_FILE" 2>/dev/null || {
            log_warning "Failed to activate temporary swap"
            sudo rm -f "$TEMP_SWAP_FILE"
            return 1
        }
        
        log_success "Temporary swap file created: ${TEMP_SWAP_SIZE}MB"
        echo "$TEMP_SWAP_FILE" > /tmp/storytellerpi_temp_swap_file
    else
        log_warning "Skipping swap creation due to insufficient space"
    fi
}

increase_swap() {
    if $IS_DIETPI; then
        increase_swap_dietpi
    else
        increase_swap_standard
    fi
}

restore_swap() {
    log_info "Restoring original swap configuration..."
    
    # Remove temporary swap file if it exists
    if [ -f "/tmp/storytellerpi_temp_swap_file" ]; then
        TEMP_SWAP_FILE=$(cat /tmp/storytellerpi_temp_swap_file)
        if [ -f "$TEMP_SWAP_FILE" ]; then
            sudo swapoff "$TEMP_SWAP_FILE" 2>/dev/null || true
            sudo rm -f "$TEMP_SWAP_FILE"
            log_info "Temporary swap file removed"
        fi
        rm -f /tmp/storytellerpi_temp_swap_file
    fi
    
    # Restore original dphys-swapfile config if it exists
    if [ -f /etc/dphys-swapfile.backup ]; then
        sudo cp /etc/dphys-swapfile.backup /etc/dphys-swapfile
        sudo rm /etc/dphys-swapfile.backup
        
        # Restart swap with original settings
        sudo dphys-swapfile swapoff 2>/dev/null || true
        sudo dphys-swapfile setup 2>/dev/null || true
        sudo dphys-swapfile swapon 2>/dev/null || true
        
        log_success "Original swap configuration restored"
    else
        log_info "No original swap configuration to restore"
    fi
}

install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install essential packages
    PACKAGES=(
        "python3-pip"
        "python3-dev"
        "python3-venv"
        "build-essential"
        "pkg-config"
        "portaudio19-dev"
        "libasound2-dev"
        "git"
        "curl"
        "systemd"
        "logrotate"
    )
    
    # Audio packages
    AUDIO_PACKAGES=(
        "alsa-utils"
        "espeak-ng"
    )
    
    # Install packages with error handling
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log_info "Installing $package..."
            sudo apt install -y "$package" || {
                log_error "Failed to install $package"
                exit 1
            }
        else
            log_info "$package already installed"
        fi
    done
    
    # Install audio packages (optional)
    for package in "${AUDIO_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log_info "Installing $package..."
            sudo apt install -y "$package" || {
                log_warning "Failed to install $package (continuing anyway)"
            }
        fi
    done
    
    # PulseAudio is optional for DietPi
    if ! $IS_DIETPI; then
        sudo apt install -y pulseaudio pulseaudio-utils || {
            log_warning "Failed to install PulseAudio (continuing with ALSA)"
        }
    fi
    
    log_success "System dependencies installed"
}

create_user_and_directories() {
    log_info "Creating user and directories..."
    
    # Create system user
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Created user: $SERVICE_USER"
    else
        log_info "User $SERVICE_USER already exists"
    fi
    
    # Create directories
    sudo mkdir -p "$INSTALL_DIR"/{main,models,logs,credentials}
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    log_success "Directories created"
}

setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment
    sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
    
    # Activate virtual environment and upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    
    # Configure pip for piwheels (faster on Pi)
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" config set global.extra-index-url https://www.piwheels.org/simple
    
    log_success "Python environment created"
}

install_python_dependencies() {
    log_info "Installing Python dependencies (this may take a while)..."
    
    # Copy requirements file
    sudo cp requirements_pi_zero.txt "$INSTALL_DIR/"
    sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/requirements_pi_zero.txt"
    
    # Install dependencies one by one to avoid memory issues
    log_info "Installing core dependencies..."
    
    # Essential packages first
    CORE_PACKAGES=(
        "python-dotenv==1.0.0"
        "psutil==5.9.6"
        "requests==2.31.0"
        "Flask==2.3.3"
        "Werkzeug==2.3.7"
        "Jinja2==3.1.2"
        "PyAudio==0.2.11"
        "pygame==2.5.2"
    )
    
    for package in "${CORE_PACKAGES[@]}"; do
        log_info "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || {
            log_error "Failed to install $package"
            exit 1
        }
    done
    
    # Wake word detection (Porcupine)
    log_info "Installing wake word detection..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary pvporcupine==3.0.1 || {
        log_warning "Failed to install Porcupine - you'll need to install it manually"
    }
    
    # AI services
    log_info "Installing AI services..."
    AI_PACKAGES=(
        "google-cloud-speech==2.21.0"
        "google-generativeai==0.3.2"
        "google-auth==2.23.4"
    )
    
    for package in "${AI_PACKAGES[@]}"; do
        log_info "Installing $package..."
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary "$package" || {
            log_warning "Failed to install $package - you may need to install it manually"
        }
    done
    
    log_success "Python dependencies installed"
}

copy_application_files() {
    log_info "Copying application files..."
    
    # Copy main application files
    sudo cp main/storyteller_main_optimized.py "$INSTALL_DIR/main/storyteller_main.py"
    sudo cp main/wake_word_detector_optimized.py "$INSTALL_DIR/main/wake_word_detector.py"
    sudo cp main/web_interface_lite.py "$INSTALL_DIR/main/web_interface.py"
    
    # Copy other service files if they exist
    for file in stt_service.py storyteller_llm.py tts_service.py audio_feedback.py; do
        if [ -f "main/$file" ]; then
            sudo cp "main/$file" "$INSTALL_DIR/main/"
        else
            log_warning "File main/$file not found - you may need to copy it manually"
        fi
    done
    
    # Copy templates
    if [ -d "main/templates" ]; then
        sudo cp -r main/templates "$INSTALL_DIR/main/"
    else
        log_warning "Templates directory not found - you may need to copy it manually"
    fi
    
    # Copy static files if they exist
    if [ -d "main/static" ]; then
        sudo cp -r main/static "$INSTALL_DIR/main/"
    fi
    
    # Copy models if they exist
    if [ -d "models" ]; then
        sudo cp models/* "$INSTALL_DIR/models/" 2>/dev/null || true
    fi
    
    # Copy scripts
    if [ -d "scripts" ]; then
        sudo cp -r scripts "$INSTALL_DIR/"
    fi
    
    # Set permissions
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo chmod +x "$INSTALL_DIR/main/storyteller_main.py"
    
    log_success "Application files copied"
}

create_configuration() {
    log_info "Creating configuration files..."
    
    # Create optimized .env file for Pi Zero 2W
    cat > /tmp/storytellerpi.env << EOF
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

# Wake word detection (Porcupine optimized)
WAKE_WORD_FRAMEWORK=porcupine
WAKE_WORD_MODEL_PATH=$INSTALL_DIR/models/hey_elsa.ppn
WAKE_WORD_THRESHOLD=0.5
WAKE_WORD_SAMPLE_RATE=16000
WAKE_WORD_BUFFER_SIZE=512
WAKE_WORD_CHANNELS=1

# Audio settings
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# AI Services (requires API keys)
# Set these after installation:
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=$INSTALL_DIR/credentials/google-cloud-key.json
# PORCUPINE_ACCESS_KEY=your-porcupine-key

# Web interface
WEB_SECRET_KEY=storytellerpi-dietpi-$(date +%s)
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_INTERFACE=lite

# Service settings
SERVICE_NAME=$SERVICE_NAME
SERVICE_USER=$SERVICE_USER

# DietPi specific optimizations
DIETPI_OPTIMIZED=true
EOF
    
    # Move to install directory
    sudo mv /tmp/storytellerpi.env "$INSTALL_DIR/.env"
    sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    
    log_success "Configuration created"
}

create_systemd_service() {
    log_info "Creating systemd service..."
    
    # Create service file
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

# Memory and CPU limits for Pi Zero 2W
MemoryMax=350M
CPUQuota=85%

# Environment
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    # Install service
    sudo mv /tmp/storytellerpi.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    log_success "Systemd service created"
}

setup_web_service() {
    log_info "Setting up web interface service..."
    
    # Create web service file
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

# Memory limit for web interface
MemoryMax=80M

# Environment
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
    
    # Install web service
    sudo mv /tmp/storytellerpi-web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    log_success "Web interface service created"
}

configure_audio() {
    log_info "Configuring audio..."
    
    # Add user to audio group
    sudo usermod -a -G audio "$SERVICE_USER"
    
    # Configure audio based on system
    if $IS_DIETPI; then
        log_info "Configuring audio for DietPi..."
        # DietPi typically uses ALSA by default
        # No additional PulseAudio configuration needed
    else
        # Configure PulseAudio for system mode if available
        if command -v pulseaudio >/dev/null 2>&1; then
            sudo sed -i 's/^; system-instance = no/system-instance = yes/' /etc/pulse/system.pa 2>/dev/null || true
        fi
    fi
    
    # Basic audio test
    if command -v speaker-test >/dev/null 2>&1; then
        log_info "Audio system configured. Test with: speaker-test -t sine -f 1000 -l 1"
    fi
    
    log_success "Audio configuration completed"
}

setup_logrotate() {
    log_info "Setting up log rotation..."
    
    # Create logrotate configuration
    cat > /tmp/storytellerpi-logrotate << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload-or-restart $SERVICE_NAME >/dev/null 2>&1 || true
    endscript
}
EOF
    
    sudo mv /tmp/storytellerpi-logrotate /etc/logrotate.d/storytellerpi
    
    log_success "Log rotation configured"
}

cleanup_installation() {
    log_info "Cleaning up installation..."
    
    # Clear pip cache
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" cache purge 2>/dev/null || true
    
    # Clear apt cache
    sudo apt clean
    sudo apt autoremove -y
    
    # Restore original swap settings
    restore_swap
    
    log_success "Installation cleanup completed"
}

print_next_steps() {
    log_success "StorytellerPi installation completed!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Configure API keys in: $INSTALL_DIR/.env"
    echo "   - Add your Porcupine access key"
    echo "   - Add your Google Cloud credentials"
    echo
    echo "2. Copy your wake word model to: $INSTALL_DIR/models/"
    echo
    echo "3. Start the services:"
    echo "   sudo systemctl enable storytellerpi-web"
    echo "   sudo systemctl start storytellerpi-web"
    echo "   sudo systemctl enable storytellerpi"
    echo "   sudo systemctl start storytellerpi"
    echo
    echo "4. Access the web interface at: http://$(hostname -I | awk '{print $1}'):5000"
    echo
    echo "5. Monitor the service:"
    echo "   sudo journalctl -u storytellerpi -f"
    echo
    echo -e "${YELLOW}DietPi specific notes:${NC}"
    echo "- Audio is configured for ALSA (no PulseAudio)"
    echo "- Memory limits are conservative for Pi Zero 2W"
    echo "- Use the lite web interface for best performance"
    echo
    echo -e "${YELLOW}Memory optimization tips:${NC}"
    echo "- Monitor memory usage: watch -n 1 free -m"
    echo "- Adjust MAX_MEMORY_USAGE in .env if needed"
    echo "- Use memory monitor: python3 $INSTALL_DIR/scripts/memory_monitor.py"
    echo
    echo -e "${GREEN}Installation directory: $INSTALL_DIR${NC}"
    echo -e "${GREEN}Service user: $SERVICE_USER${NC}"
    echo -e "${GREEN}System type: $([ $IS_DIETPI == true ] && echo "DietPi" || echo "Standard Linux")${NC}"
}

# Main installation process
main() {
    log_info "Starting StorytellerPi installation for Pi Zero 2W..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Installation steps
    detect_system
    check_pi_zero
    increase_swap
    install_system_dependencies
    create_user_and_directories
    setup_python_environment
    install_python_dependencies
    copy_application_files
    create_configuration
    create_systemd_service
    setup_web_service
    configure_audio
    setup_logrotate
    cleanup_installation
    print_next_steps
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@"