#!/bin/bash

# Quick fix for DietPi setup - continues from where setup_pi_zero.sh failed
# This script handles the swap issue and continues installation

set -e

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

create_temporary_swap() {
    log_info "Creating temporary swap file for installation..."
    
    # Check current swap
    CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
    log_info "Current swap: ${CURRENT_SWAP}MB"
    
    if [ "$CURRENT_SWAP" -lt 512 ]; then
        # Create temporary swap file
        TEMP_SWAP_FILE="/tmp/storytellerpi_install_swap"
        TEMP_SWAP_SIZE="512"
        
        # Check available space
        AVAILABLE_SPACE=$(df /tmp | awk 'NR==2 {print int($4/1024)}')
        if [ "$AVAILABLE_SPACE" -lt "$TEMP_SWAP_SIZE" ]; then
            log_warning "Insufficient space for 512MB swap, using smaller size"
            TEMP_SWAP_SIZE=$((AVAILABLE_SPACE - 100))
        fi
        
        if [ "$TEMP_SWAP_SIZE" -gt 100 ]; then
            log_info "Creating ${TEMP_SWAP_SIZE}MB temporary swap file..."
            
            # Create and activate swap file
            sudo dd if=/dev/zero of="$TEMP_SWAP_FILE" bs=1M count="$TEMP_SWAP_SIZE" 2>/dev/null
            sudo chmod 600 "$TEMP_SWAP_FILE"
            sudo mkswap "$TEMP_SWAP_FILE" >/dev/null 2>&1
            sudo swapon "$TEMP_SWAP_FILE"
            
            log_success "Temporary swap file created and activated"
            echo "$TEMP_SWAP_FILE" > /tmp/storytellerpi_temp_swap_file
            
            # Show new swap status
            free -m
        else
            log_warning "Skipping swap creation - insufficient space"
        fi
    else
        log_info "Sufficient swap space already available"
    fi
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
        alsa-utils \
        git \
        curl \
        systemd \
        logrotate \
        espeak-ng
    
    log_success "System dependencies installed"
}

continue_installation() {
    log_info "Continuing StorytellerPi installation for DietPi..."
    
    # Create temporary swap if needed
    create_temporary_swap
    
    # Install system dependencies
    install_system_dependencies
    
    # Create user and directories
    log_info "Creating user and directories..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Created user: $SERVICE_USER"
    fi
    
    sudo mkdir -p "$INSTALL_DIR"/{main,models,logs,credentials}
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    # Setup Python environment
    log_info "Setting up Python environment..."
    sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" config set global.extra-index-url https://www.piwheels.org/simple
    
    # Install core Python packages
    log_info "Installing core Python packages..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary \
        python-dotenv==1.0.0 \
        psutil==5.9.6 \
        requests==2.31.0 \
        Flask==2.3.3 \
        Werkzeug==2.3.7 \
        Jinja2==3.1.2
    
    # Install audio packages
    log_info "Installing audio packages..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary \
        PyAudio==0.2.11 \
        pygame==2.5.2
    
    # Install wake word detection
    log_info "Installing Porcupine..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary \
        pvporcupine==3.0.1 || log_warning "Porcupine installation failed - install manually later"
    
    # Install AI services
    log_info "Installing AI services..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --no-cache-dir --prefer-binary \
        google-cloud-speech==2.21.0 \
        google-generativeai==0.3.2 \
        google-auth==2.23.4 || log_warning "Some AI services failed to install"
    
    log_success "Python packages installed"
}

cleanup_swap() {
    log_info "Cleaning up temporary swap..."
    
    if [ -f "/tmp/storytellerpi_temp_swap_file" ]; then
        TEMP_SWAP_FILE=$(cat /tmp/storytellerpi_temp_swap_file)
        if [ -f "$TEMP_SWAP_FILE" ]; then
            sudo swapoff "$TEMP_SWAP_FILE" 2>/dev/null || true
            sudo rm -f "$TEMP_SWAP_FILE"
            log_info "Temporary swap file removed"
        fi
        rm -f /tmp/storytellerpi_temp_swap_file
    fi
}

# Trap to cleanup on exit
trap cleanup_swap EXIT

# Main execution
log_info "DietPi Setup Fix - Continuing StorytellerPi Installation"
continue_installation

log_success "Installation continued successfully!"
log_info "You can now run the full DietPi setup script:"
log_info "chmod +x setup_pi_zero_dietpi.sh"
log_info "sudo ./setup_pi_zero_dietpi.sh"
log_info ""
log_info "Or continue manually by copying the application files and configuring services."