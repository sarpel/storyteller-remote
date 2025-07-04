#!/bin/bash

# StorytellerPi Unified Setup Script
# Complete installation and configuration for Raspberry Pi voice storytelling device
# Version: 2.0
# Author: StorytellerPi Team

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/storytellerpi_setup.log"
INSTALL_DIR="/opt/storytellerpi"
SERVICE_USER="storyteller"
PYTHON_VERSION="3.9"

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

# Help function
show_help() {
    cat << EOF
StorytellerPi Setup Script v2.0

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

EXAMPLES:
    sudo ./setup.sh                    # Production installation
    sudo ./setup.sh --development      # Development installation
    sudo ./setup.sh --audio-only       # Audio setup only
    sudo ./setup.sh --clean            # Clean install

For more information, see README.md
EOF
}

# Installation type (default to production)
INSTALL_TYPE="production"
CLEAN_INSTALL=false
RESUME_INSTALL=false

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
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

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

# System validation
check_raspberry_pi() {
    print_status "Checking if running on Raspberry Pi..."
    
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "Not running on Raspberry Pi - some features may not work"
    else
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
        print_success "Detected: $PI_MODEL"
    fi
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

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
    
    print_status "Updating system packages..."
    apt update && apt upgrade -y
    
    print_status "Installing system dependencies..."
    apt install -y \
        python3 python3-pip python3-venv python3-dev \
        build-essential pkg-config \
        portaudio19-dev libasound2-dev \
        git curl wget \
        ffmpeg espeak \
        systemd
    
    print_status "Creating service user..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    fi
    
    print_status "Creating installation directory..."
    mkdir -p "$INSTALL_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    save_progress "phase1"
    print_success "Phase 1 completed"
}

# Phase 2: Audio setup
phase2_audio_setup() {
    print_header "Phase 2: Audio Setup"
    
    if [[ "$INSTALL_TYPE" == "test-only" ]] || [[ "$INSTALL_TYPE" == "quick" ]]; then
        print_status "Skipping audio setup for $INSTALL_TYPE mode"
        return
    fi
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase2" ]]; then
        print_status "Skipping Phase 2 (already completed)"
        return
    fi
    
    print_status "Configuring IQaudIO Pi-Codec Zero HAT..."
    
    # Enable I2S interface
    if ! grep -q "dtparam=i2s=on" /boot/config.txt; then
        echo "dtparam=i2s=on" >> /boot/config.txt
    fi
    
    # Add IQaudIO overlay
    if ! grep -q "dtoverlay=iqaudio-codec" /boot/config.txt; then
        echo "dtoverlay=iqaudio-codec" >> /boot/config.txt
    fi
    
    # Configure ALSA
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
    
    print_status "Testing audio configuration..."
    # Test will be done later in validation phase
    
    save_progress "phase2"
    print_success "Phase 2 completed"
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
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        print_status "Installing Python dependencies..."
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    save_progress "phase3"
    print_success "Phase 3 completed"
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
    cp -r "$SCRIPT_DIR/main" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/models" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/tests" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
    
    # Create directories
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/credentials"
    
    # Copy configuration template
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/.env"
    else
        # Create basic .env template
        cat > "$INSTALL_DIR/.env" << 'EOF'
# StorytellerPi Configuration
# Copy this file and configure your API keys

# Installation Settings
INSTALL_DIR=/opt/storytellerpi
LOG_DIR=/opt/storytellerpi/logs

# API Keys (Required)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
PORCUPINE_ACCESS_KEY=your-porcupine-access-key-here
EOF
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
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/main"/*.py
    
    save_progress "phase4"
    print_success "Phase 4 completed"
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
    
    print_status "Creating systemd service..."
    
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

# Resource limits for Pi Zero 2W
MemoryLimit=400M
CPUQuota=80%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/temp

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable storytellerpi
    
    # Set up web interface service
    print_status "Creating web interface service..."
    
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

# Resource limits for Pi Zero 2W
MemoryLimit=200M
CPUQuota=50%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable web interface service
    systemctl daemon-reload
    systemctl enable storytellerpi-web
    
    # Set up log rotation
    cat > /etc/logrotate.d/storytellerpi << 'EOF'
/opt/storytellerpi/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 storyteller storyteller
    postrotate
        systemctl reload storytellerpi || true
    endscript
}
EOF
    
    save_progress "phase5"
    print_success "Phase 5 completed"
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
        print_success "Audio system: OK"
    else
        print_warning "Audio system: NOT CONFIGURED"
    fi
    
    # Test application files
    if [[ -f "$INSTALL_DIR/main/storyteller_main.py" ]]; then
        print_success "Application files: OK"
    else
        print_error "Application files: MISSING"
    fi
    
    # Test web interface
    if [[ -f "$INSTALL_DIR/main/web_interface.py" ]]; then
        print_success "Web interface: OK"
    else
        print_warning "Web interface: MISSING"
    fi
    
    # Test audio feedback
    if [[ -f "$INSTALL_DIR/main/audio_feedback.py" ]]; then
        print_success "Audio feedback: OK"
    else
        print_warning "Audio feedback: MISSING"
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

=== Installation Status ===
Installation Directory: $INSTALL_DIR
Service User: $SERVICE_USER
Log Directory: $INSTALL_DIR/logs

=== Services ===
EOF
    
    # Check service status
    if systemctl list-unit-files | grep -q storytellerpi.service; then
        cat >> "$REPORT_FILE" << 'EOF'
Main Service: INSTALLED
EOF
    fi
    
    if systemctl list-unit-files | grep -q storytellerpi-web.service; then
        cat >> "$REPORT_FILE" << 'EOF'
Web Interface: INSTALLED
EOF
    fi
    
    cat >> "$REPORT_FILE" << 'EOF'

=== Next Steps ===
1. Configure API keys in /opt/storytellerpi/.env
2. Access web interface at http://[PI_IP]:8080
3. Start services: sudo systemctl start storytellerpi storytellerpi-web
4. Check logs: sudo journalctl -u storytellerpi -f
EOF
    
    cat "$REPORT_FILE"
    
    print_status "Full report saved to: $REPORT_FILE"
}

# Main installation flow
main() {
    print_header "StorytellerPi Unified Setup v2.0"
    
    print_status "Installation type: $INSTALL_TYPE"
    print_status "Log file: $LOG_FILE"
    
    # Initialize log (create in script directory to avoid permission issues)
    echo "StorytellerPi Setup Started: $(date)" > "$LOG_FILE" 2>/dev/null || {
        LOG_FILE="./storytellerpi_setup.log"
        echo "StorytellerPi Setup Started: $(date)" > "$LOG_FILE"
        print_status "Using local log file: $LOG_FILE"
    }
    
    # Check environment
    check_raspberry_pi
    
    # Clean if requested
    cleanup_old_install
    
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
    
    # Final status
    print_success "StorytellerPi setup completed successfully!"
    
    if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "audio-only" ]]; then
        print_warning "Reboot recommended to ensure all changes take effect"
        print_status "Run: sudo reboot"
    fi
    
    # Cleanup progress file
    rm -f "$PROGRESS_FILE"
}

# Run main function
main "$@"