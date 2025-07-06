#!/bin/bash

# =============================================================================
# StorytellerPi Testing Mode Setup Script
# Enables/disables wake word testing mode for development
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
SERVICE_NAME="storytellerpi"

log_info() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[SETUP]${NC} $1"
}

log_error() {
    echo -e "${RED}[SETUP]${NC} $1"
}

show_usage() {
    cat << EOF
Testing Mode Setup for StorytellerPi

USAGE:
    $0 [enable|disable|status]

COMMANDS:
    enable      - Enable testing mode
    disable     - Disable testing mode
    status      - Show current testing mode status

DESCRIPTION:
    This script enables/disables wake word testing mode for development.
    When enabled, you can trigger wake word detection using:
    
    Bash: ./scripts/test_wake_word.sh
    Python: python3 ./scripts/test_wake_word.py
    
    ⚠️  WARNING: Testing mode should be DISABLED in production!

EOF
}

check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found: $ENV_FILE"
        return 1
    fi
    return 0
}

get_current_status() {
    if ! check_env_file; then
        return 1
    fi
    
    local status=$(grep "^WAKE_WORD_TESTING_MODE=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')
    echo "$status"
}

enable_testing_mode() {
    log_info "Enabling wake word testing mode..."
    
    if ! check_env_file; then
        return 1
    fi
    
    # Update .env file
    if grep -q "^WAKE_WORD_TESTING_MODE=" "$ENV_FILE"; then
        # Replace existing line
        sed -i 's/^WAKE_WORD_TESTING_MODE=.*/WAKE_WORD_TESTING_MODE=true/' "$ENV_FILE"
    else
        # Add new line
        echo "" >> "$ENV_FILE"
        echo "# Testing Mode (REMOVE IN PRODUCTION!)" >> "$ENV_FILE"
        echo "WAKE_WORD_TESTING_MODE=true" >> "$ENV_FILE"
        echo "WAKE_WORD_TEST_TRIGGER_FILE=/tmp/storyteller_wake_trigger" >> "$ENV_FILE"
    fi
    
    # Make test scripts executable
    chmod +x "$SCRIPT_DIR/test_wake_word.sh" 2>/dev/null
    chmod +x "$SCRIPT_DIR/test_wake_word.py" 2>/dev/null
    
    log_success "Testing mode enabled!"
    log_warn "⚠️  Remember to restart StorytellerPi service for changes to take effect"
    log_info "Restart command: sudo systemctl restart $SERVICE_NAME"
    log_info ""
    log_info "Test commands:"
    log_info "  Bash:   ./scripts/test_wake_word.sh"
    log_info "  Python: python3 ./scripts/test_wake_word.py"
}

disable_testing_mode() {
    log_info "Disabling wake word testing mode..."
    
    if ! check_env_file; then
        return 1
    fi
    
    # Update .env file
    if grep -q "^WAKE_WORD_TESTING_MODE=" "$ENV_FILE"; then
        sed -i 's/^WAKE_WORD_TESTING_MODE=.*/WAKE_WORD_TESTING_MODE=false/' "$ENV_FILE"
    fi
    
    # Clean up any existing trigger files
    sudo rm -f /tmp/storyteller_wake_trigger 2>/dev/null
    
    log_success "Testing mode disabled!"
    log_warn "⚠️  Remember to restart StorytellerPi service for changes to take effect"
    log_info "Restart command: sudo systemctl restart $SERVICE_NAME"
}

show_status() {
    log_info "Checking testing mode status..."
    
    local status=$(get_current_status)
    
    if [[ "$status" == "true" ]]; then
        log_success "Testing mode is ENABLED"
        log_warn "⚠️  This should be DISABLED in production!"
        
        # Check if service is running and using testing mode
        if systemctl is-active $SERVICE_NAME >/dev/null 2>&1; then
            log_info "StorytellerPi service is running"
            
            if [[ -p "/tmp/storyteller_wake_trigger" ]]; then
                log_success "Test trigger is active and ready"
                log_info "You can use test scripts to trigger wake word detection"
            else
                log_warn "Service is running but test trigger not found"
                log_info "Service may need restart to activate testing mode"
            fi
        else
            log_warn "StorytellerPi service is not running"
        fi
        
    elif [[ "$status" == "false" ]]; then
        log_info "Testing mode is DISABLED"
        log_success "✅ Safe for production"
        
    else
        log_warn "Testing mode status unclear or not configured"
        log_info "Current value: $status"
    fi
    
    log_info ""
    log_info "Available test commands:"
    log_info "  ./scripts/test_wake_word.sh --help"
    log_info "  python3 ./scripts/test_wake_word.py --help"
}

main() {
    case "${1:-status}" in
        enable)
            enable_testing_mode
            ;;
        disable)
            disable_testing_mode
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Check if running in project directory
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "Please run this script from the StorytellerPi project directory"
    exit 1
fi

main "$@"