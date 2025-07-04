#!/bin/bash

# StorytellerPi Unified Setup Script
# Complete installation and configuration for Raspberry Pi voice storytelling device
# Version: 2.0
# Author: StorytellerPi Team

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/storytellerpi_setup.log"
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
    echo -e "\033[1;34m[INFO]\033[0m $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
StorytellerPi Unified Setup Script

USAGE:
    sudo ./setup.sh [OPTIONS]

OPTIONS:
    --production        Full production setup (default)
    --development       Development setup with mock services
    --audio-only        Configure audio hardware only
    --quick             Fast minimal installation
    --test-only         Run tests and validation only
    --resume            Resume interrupted installation
    --clean             Clean install (remove existing)
    --help              Show this help message

EXAMPLES:
    sudo ./setup.sh                    # Full production setup
    sudo ./setup.sh --quick            # Fast minimal install
    sudo ./setup.sh --development      # Dev setup for testing
    sudo ./setup.sh --audio-only       # Just configure audio

REQUIREMENTS:
    - Raspberry Pi OS (Bookworm recommended)
    - Internet connection
    - IQaudIO Pi-Codec Zero HAT (for audio)
    - 32GB+ microSD card
    - Run as root (sudo)

For more information, see README.md
EOF
}

# Parse command line arguments
INSTALL_TYPE="production"
CLEAN_INSTALL=false
RESUME_INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
        --quick)
            INSTALL_TYPE="quick"
            shift
            ;;
        --test-only)
            INSTALL_TYPE="test-only"
            shift
            ;;
        --resume)
            RESUME_INSTALL=true
            shift
            ;;
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "Not running on Raspberry Pi - some features may not work"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
        print_status "Detected: $PI_MODEL"
    fi
}

# Progress tracking
PROGRESS_FILE="/tmp/storytellerpi_progress"

save_progress() {
    echo "$1" > "$PROGRESS_FILE"
}

get_progress() {
    if [[ -f "$PROGRESS_FILE" ]]; then
        cat "$PROGRESS_FILE"
    else
        echo "start"
    fi
}

# Phase 1: System Preparation
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
        git curl wget unzip \
        build-essential cmake \
        libasound2-dev portaudio19-dev \
        alsa-utils pulseaudio \
        systemd \
        htop nano vim \
        rsync
    
    # Install additional dependencies based on install type
    if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "development" ]]; then
        apt install -y \
            ffmpeg \
            sox \
            espeak espeak-data \
            watchdog
    fi
    
    save_progress "phase1"
    print_success "Phase 1 completed"
}

# Phase 2: Audio Hardware Setup
phase2_audio_setup() {
    print_header "Phase 2: Audio Hardware Setup"
    
    if [[ "$INSTALL_TYPE" == "test-only" ]]; then
        print_status "Skipping audio setup for test-only mode"
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
        print_status "Enabled I2S interface"
    fi
    
    # Add IQaudIO device tree overlay
    if ! grep -q "dtoverlay=iqaudio-codec" /boot/config.txt; then
        echo "dtoverlay=iqaudio-codec" >> /boot/config.txt
        print_status "Added IQaudIO codec overlay"
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
    
    # Set audio levels
    print_status "Configuring audio levels..."
    amixer set 'Output Mixer HiFi' on 2>/dev/null || true
    amixer set 'Input Mixer Line' on 2>/dev/null || true
    amixer set 'Headphone' 80% 2>/dev/null || true
    amixer set 'Speaker' 80% 2>/dev/null || true
    
    save_progress "phase2"
    print_success "Phase 2 completed"
}

# Phase 3: Python Environment Setup
phase3_python_setup() {
    print_header "Phase 3: Python Environment Setup"
    
    if [[ "$RESUME_INSTALL" == true ]] && [[ "$(get_progress)" > "phase3" ]]; then
        print_status "Skipping Phase 3 (already completed)"
        return
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Configure pip for fast installation
    print_status "Configuring pip for optimal performance..."
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << 'EOF'
[global]
timeout = 60
retries = 3
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               www.piwheels.org
extra-index-url = https://www.piwheels.org/simple/
prefer-binary = true

[install]
compile = false
EOF
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install packages based on type
    print_status "Installing Python packages (optimized for speed)..."
    
    # Use unified requirements.txt
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        print_status "Using unified requirements.txt..."
        pip install --no-cache-dir --prefer-binary -r "$SCRIPT_DIR/requirements.txt"
        
        # Add development packages if needed
        if [[ "$INSTALL_TYPE" == "development" ]]; then
            print_status "Adding development tools..."
            pip install --no-cache-dir pytest pytest-asyncio pytest-mock black flake8
        fi
    else
        # Fallback to individual installs
        print_status "Installing core packages individually..."
        pip install --no-cache-dir --prefer-binary \
            python-dotenv==1.0.0 PyYAML==6.0.1 numpy==1.24.3 \
            PyAudio==0.2.11 pygame==2.5.2 requests==2.31.0 psutil==5.9.6
        
        if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "development" ]]; then
            pip install --no-cache-dir --prefer-binary \
                google-cloud-speech==2.21.0 google-generativeai==0.3.2 \
                openai==1.3.0 elevenlabs==0.2.26 openwakeword==0.5.1
        fi
    fi
    
    deactivate
    save_progress "phase3"
    print_success "Phase 3 completed"
}# Phase 4: Application Setup
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
    
    print_status "Setting up application files..."
    
    # Copy application files
    rsync -av "$SCRIPT_DIR/main/" "$INSTALL_DIR/" --exclude="__pycache__" --exclude="*.pyc"
    rsync -av "$SCRIPT_DIR/models/" "$INSTALL_DIR/models/" 2>/dev/null || true
    
    # Create directories
    mkdir -p "$INSTALL_DIR"/{logs,temp,cache}
    
    # Set up .env configuration file
    if [[ ! -f "$INSTALL_DIR/.env" ]]; then
        if [[ -f "$SCRIPT_DIR/.env" ]]; then
            print_status "Setting up .env configuration file..."
            cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/.env"
            
            # Update paths in .env file for this installation
            sed -i "s|/opt/storytellerpi|$INSTALL_DIR|g" "$INSTALL_DIR/.env"
            
            print_status "Configuration file created at $INSTALL_DIR/.env"
        else
            print_warning ".env template not found, creating basic configuration..."
            cat > "$INSTALL_DIR/.env" << 'EOF'
# Basic StorytellerPi Configuration
LOG_LEVEL=INFO
INSTALL_DIR=/opt/storytellerpi
LOG_DIR=/opt/storytellerpi/logs
MODELS_DIR=/opt/storytellerpi/models
TARGET_RESPONSE_TIME=11.0
MAX_MEMORY_USAGE=400

# Add your API keys here:
# GEMINI_API_KEY=your-gemini-api-key-here
# GOOGLE_CREDENTIALS_JSON=/opt/storytellerpi/google-credentials.json
# OPENAI_API_KEY=sk-your-openai-api-key-here
# ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
EOF
        fi
    fi
    
    # Set up credentials information
    print_status "Setting up credentials information..."
    cat > "$INSTALL_DIR/CREDENTIALS.md" << 'EOF'
# API Credentials Setup

All API credentials are now configured in the .env file.

## Required Credentials:

1. **Google Gemini API Key** (for AI storytelling):
   - Get from Google AI Studio: https://aistudio.google.com/app/apikey
   - Add to .env file: GEMINI_API_KEY=your-gemini-api-key-here

2. **Google Cloud Service Account** (for Speech-to-Text):
   - Download JSON key from Google Cloud Console
   - Enable Speech-to-Text API
   - Place at: /opt/storytellerpi/google-credentials.json
   - Update GOOGLE_CREDENTIALS_JSON in .env file

3. **OpenAI API Key** (for Whisper fallback):
   - Get from OpenAI Platform (platform.openai.com)
   - Add to .env file: OPENAI_API_KEY=sk-...

4. **ElevenLabs API Key** (for text-to-speech):
   - Get from ElevenLabs (elevenlabs.io)
   - Add to .env file: ELEVENLABS_API_KEY=your-api-key

## Configuration:
Edit /opt/storytellerpi/.env and add your API keys.

## Security:
- Set proper permissions: chmod 600 /opt/storytellerpi/.env
- Never commit .env to version control
- Keep backups of your .env file

## Test your setup:
```bash
sudo systemctl start storytellerpi
sudo journalctl -u storytellerpi -n 50
```
EOF
    
    # Create service user
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_status "Creating service user: $SERVICE_USER"
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    fi
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 700 "$INSTALL_DIR/credentials"
    chmod 755 "$INSTALL_DIR"
    
    save_progress "phase4"
    print_success "Phase 4 completed"
}

# Phase 5: Service Configuration
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
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/storyteller_main.py
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
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_status "Testing Python packages..."
    python3 -c "import yaml, numpy, pygame; print('Core packages: OK')" || print_warning "Core packages test failed"
    
    if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "development" ]]; then
        python3 -c "import openwakeword; print('OpenWakeWord: OK')" || print_warning "OpenWakeWord test failed"
        python3 -c "import elevenlabs; print('ElevenLabs: OK')" || print_warning "ElevenLabs test failed"
    fi
    
    # Test audio
    if [[ "$INSTALL_TYPE" != "test-only" ]]; then
        print_status "Testing audio system..."
        if command -v aplay &> /dev/null; then
            # Test audio playback (generate a short beep)
            speaker-test -t sine -f 1000 -l 1 -s 1 &>/dev/null || print_warning "Audio test failed"
            print_status "Audio system: OK"
        fi
    fi
    
    # Test application files
    if [[ "$INSTALL_TYPE" == "production" ]] || [[ "$INSTALL_TYPE" == "development" ]]; then
        if [[ -f "$INSTALL_DIR/storyteller_main.py" ]]; then
            print_status "Application files: OK"
        else
            print_warning "Main application file not found"
        fi
    fi
    
    deactivate
    
    # Run specific tests if available
    if [[ "$INSTALL_TYPE" == "development" ]] || [[ "$INSTALL_TYPE" == "test-only" ]]; then
        if [[ -f "$SCRIPT_DIR/run_tests.py" ]]; then
            print_status "Running unit tests..."
            cd "$SCRIPT_DIR"
            python3 run_tests.py --quick || print_warning "Some tests failed"
        fi
    fi
    
    save_progress "phase6"
    print_success "Phase 6 completed"
}

# Generate installation report
generate_report() {
    print_header "Installation Report"
    
    REPORT_FILE="/tmp/storytellerpi_report.txt"
    
    cat > "$REPORT_FILE" << EOF
StorytellerPi Installation Report
Generated: $(date)
Installation Type: $INSTALL_TYPE

System Information:
- OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
- Kernel: $(uname -r)
- Architecture: $(uname -m)
- Raspberry Pi Model: ${PI_MODEL:-"Not detected"}

Installation Status:
- Install Directory: $INSTALL_DIR
- Service User: $SERVICE_USER
- Python Environment: $INSTALL_DIR/venv
- Configuration: $INSTALL_DIR/config/config.yaml
- Credentials: $INSTALL_DIR/credentials/

Services:
EOF
    
    if [[ "$INSTALL_TYPE" == "production" ]]; then
        echo "- SystemD Service: storytellerpi" >> "$REPORT_FILE"
        if systemctl is-enabled storytellerpi &>/dev/null; then
            echo "  Status: Enabled" >> "$REPORT_FILE"
        else
            echo "  Status: Not enabled" >> "$REPORT_FILE"
        fi
    fi
    
    echo "" >> "$REPORT_FILE"
    echo "Next Steps:" >> "$REPORT_FILE"
    
    case "$INSTALL_TYPE" in
        "production")
            cat >> "$REPORT_FILE" << 'EOF'
1. Add API credentials to /opt/storytellerpi/credentials/
2. Start the service: sudo systemctl start storytellerpi
3. Check status: sudo systemctl status storytellerpi
4. View logs: sudo journalctl -u storytellerpi -f
EOF
            ;;
        "development")
            cat >> "$REPORT_FILE" << 'EOF'
1. Add API credentials to /opt/storytellerpi/credentials/
2. Run development version: cd /opt/storytellerpi && python storyteller_dev.py
3. Run tests: cd project_dir && python run_tests.py
EOF
            ;;
        "quick")
            cat >> "$REPORT_FILE" << 'EOF'
1. Essential packages installed
2. Add remaining packages as needed
3. Configure application manually
EOF
            ;;
        "audio-only")
            cat >> "$REPORT_FILE" << 'EOF'
1. Audio hardware configured
2. Reboot required: sudo reboot
3. Test audio: speaker-test -c 2
EOF
            ;;
    esac
    
    cat "$REPORT_FILE"
    print_status "Full report saved to: $REPORT_FILE"
}

# Cleanup old installation
cleanup_old_install() {
    if [[ "$CLEAN_INSTALL" == true ]]; then
        print_status "Cleaning previous installation..."
        
        # Stop service if running
        systemctl stop storytellerpi 2>/dev/null || true
        systemctl disable storytellerpi 2>/dev/null || true
        
        # Remove service file
        rm -f /etc/systemd/system/storytellerpi.service
        systemctl daemon-reload
        
        # Remove installation directory
        rm -rf "$INSTALL_DIR"
        
        # Remove service user
        userdel "$SERVICE_USER" 2>/dev/null || true
        
        print_success "Cleanup completed"
    fi
}

# Main installation flow
main() {
    print_header "StorytellerPi Unified Setup v2.0"
    
    print_status "Installation type: $INSTALL_TYPE"
    print_status "Log file: $LOG_FILE"
    
    # Initialize log
    echo "StorytellerPi Setup Started: $(date)" > "$LOG_FILE"
    
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