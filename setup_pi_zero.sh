#!/bin/bash

# StorytellerPi Setup Script - Optimized for Raspberry Pi Zero 2W
# This script installs and configures StorytellerPi with minimal resource usage

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
SWAP_SIZE="1024"  # MB - Temporary increase for installation

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

check_pi_zero() {
    log_info "Checking if running on Raspberry Pi Zero 2W..."
    
    # Check if it's a Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
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

increase_swap() {
    log_info "Temporarily increasing swap space for installation..."
    
    # Stop swap
    sudo dphys-swapfile swapoff 2>/dev/null || true
    
    # Backup original swapfile config
    sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.backup 2>/dev/null || true
    
    # Set new swap size
    sudo sed -i "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=${SWAP_SIZE}/" /etc/dphys-swapfile
    
    # Setup and start new swap
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    log_success "Swap increased to ${SWAP_SIZE}MB"
}

restore_swap() {
    log_info "Restoring original swap configuration..."
    
    # Restore original config if backup exists
    if [ -f /etc/dphys-swapfile.backup ]; then
        sudo cp /etc/dphys-swapfile.backup /etc/dphys-swapfile
        sudo rm /etc/dphys-swapfile.backup
    else
        # Set to minimal swap for Pi Zero 2W
        sudo sed -i "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=100/" /etc/dphys-swapfile
    fi
    
    # Restart swap with original settings
    sudo dphys-swapfile swapoff
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    log_success "Swap configuration restored"
}

install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install essential packages
    sudo apt install -y \
        python3-pip \
        python3-dev \
        python3-venv \
        build-essential \
        pkg-config \
        portaudio19-dev \
        libasound2-dev \
        pulseaudio \
        pulseaudio-utils \
        alsa-utils \
        git \
        curl \
        systemd \
        logrotate
    
    # Install minimal audio tools
    sudo apt install -y espeak-ng  # Lightweight TTS fallback
    
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
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary python-dotenv==1.0.0
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary psutil==5.9.6
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary requests==2.31.0
    
    # Web interface
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary Flask==2.3.3
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary Werkzeug==2.3.7
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary Jinja2==3.1.2
    
    # Audio processing
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary PyAudio==0.2.11
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary pygame==2.5.2
    
    # Wake word detection (Porcupine)
    log_info "Installing wake word detection..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary pvporcupine==3.0.1
    
    # AI services
    log_info "Installing AI services..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary google-cloud-speech==2.21.0
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary google-generativeai==0.3.2
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary google-auth==2.23.4
    
    log_success "Python dependencies installed"
}

copy_application_files() {
    log_info "Copying application files..."
    
    # Copy main application files
    sudo cp main/storyteller_main_optimized.py "$INSTALL_DIR/main/storyteller_main.py"
    sudo cp main/wake_word_detector_optimized.py "$INSTALL_DIR/main/wake_word_detector.py"
    sudo cp main/web_interface_lite.py "$INSTALL_DIR/main/web_interface.py"
    sudo cp main/stt_service.py "$INSTALL_DIR/main/"
    sudo cp main/storyteller_llm.py "$INSTALL_DIR/main/"
    sudo cp main/tts_service.py "$INSTALL_DIR/main/"
    sudo cp main/audio_feedback.py "$INSTALL_DIR/main/"
    
    # Copy templates
    sudo cp -r main/templates "$INSTALL_DIR/main/"
    
    # Copy static files if they exist
    if [ -d "main/static" ]; then
        sudo cp -r main/static "$INSTALL_DIR/main/"
    fi
    
    # Copy models
    if [ -d "models" ]; then
        sudo cp models/* "$INSTALL_DIR/models/" 2>/dev/null || true
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
MAX_MEMORY_USAGE=350
TARGET_RESPONSE_TIME=15.0
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
WEB_SECRET_KEY=storytellerpi-pi-zero-$(date +%s)
WEB_HOST=0.0.0.0
WEB_PORT=5000

# Service settings
SERVICE_NAME=$SERVICE_NAME
SERVICE_USER=$SERVICE_USER
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
MemoryMax=400M
CPUQuota=90%

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
MemoryMax=100M

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
    
    # Configure PulseAudio for system mode
    sudo sed -i 's/^; system-instance = no/system-instance = yes/' /etc/pulse/system.pa 2>/dev/null || true
    
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
    echo -e "${YELLOW}Memory optimization tips:${NC}"
    echo "- Monitor memory usage: watch -n 1 free -m"
    echo "- Adjust MAX_MEMORY_USAGE in .env if needed"
    echo "- Use lite web interface for minimal footprint"
    echo
    echo -e "${GREEN}Installation directory: $INSTALL_DIR${NC}"
    echo -e "${GREEN}Service user: $SERVICE_USER${NC}"
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