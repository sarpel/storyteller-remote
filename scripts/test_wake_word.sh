#!/bin/bash

# =============================================================================
# StorytellerPi Wake Word Testing Script
# Simulates wake word detection for testing purposes on Raspberry Pi Zero 2W
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TRIGGER_FILE="/tmp/storyteller_wake_trigger"
SCRIPT_NAME="$(basename "$0")"
LOG_PREFIX="[WAKE-TEST]"

# Function to print colored output
log_info() {
    echo -e "${BLUE}${LOG_PREFIX}${NC} $1"
}

log_success() {
    echo -e "${GREEN}${LOG_PREFIX}${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}${LOG_PREFIX}${NC} $1"
}

log_error() {
    echo -e "${RED}${LOG_PREFIX}${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
${SCRIPT_NAME} - StorytellerPi Wake Word Testing Tool

USAGE:
    $SCRIPT_NAME [OPTIONS] [COMMAND]

COMMANDS:
    trigger                 - Trigger wake word detection (default)
    trigger-custom <word>   - Trigger with custom wake word
    trigger-low             - Trigger with low confidence (0.6)
    trigger-high            - Trigger with high confidence (0.95)
    status                  - Check if testing mode is active
    help                    - Show this help message

OPTIONS:
    -c, --confidence <val>  - Set confidence level (0.0-1.0, default: 1.0)
    -w, --word <word>       - Set wake word (default: hey_elsa)
    -v, --verbose           - Verbose output
    -q, --quiet             - Quiet mode (errors only)

EXAMPLES:
    $SCRIPT_NAME                           # Simple wake word trigger
    $SCRIPT_NAME trigger-custom "hello"    # Custom wake word
    $SCRIPT_NAME -c 0.8 -w "hey_elsa"     # Custom confidence and word
    $SCRIPT_NAME status                    # Check if testing is active

NOTES:
    - Testing mode must be enabled in StorytellerPi configuration
    - Set WAKE_WORD_TESTING_MODE=true in .env file
    - This script is for TESTING PURPOSES ONLY
    - Remove in production deployment

EOF
}

# Function to check if testing mode is active
check_testing_mode() {
    if [[ ! -p "$TRIGGER_FILE" ]]; then
        log_error "Testing mode not active or StorytellerPi not running"
        log_info "Make sure:"
        log_info "1. StorytellerPi is running"
        log_info "2. WAKE_WORD_TESTING_MODE=true in .env file"
        log_info "3. Service has been restarted after configuration change"
        return 1
    fi
    return 0
}

# Function to trigger wake word
trigger_wake_word() {
    local confidence="${1:-1.0}"
    local wake_word="${2:-hey_elsa}"
    local verbose="${3:-false}"
    
    if ! check_testing_mode; then
        return 1
    fi
    
    if [[ "$verbose" == "true" ]]; then
        log_info "Triggering wake word detection..."
        log_info "Wake word: $wake_word"
        log_info "Confidence: $confidence"
    fi
    
    # Send trigger command
    echo "WAKE $confidence $wake_word" > "$TRIGGER_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Wake word triggered successfully!"
        if [[ "$verbose" == "true" ]]; then
            log_info "Check StorytellerPi logs for detection confirmation"
        fi
        return 0
    else
        log_error "Failed to trigger wake word"
        return 1
    fi
}

# Function to show status
show_status() {
    log_info "Checking StorytellerPi testing mode status..."
    
    if [[ -p "$TRIGGER_FILE" ]]; then
        log_success "Testing mode is ACTIVE"
        log_info "Trigger file: $TRIGGER_FILE"
        log_info "You can trigger wake word detection using this script"
        
        # Check file permissions
        local perms=$(stat -c "%a" "$TRIGGER_FILE" 2>/dev/null)
        if [[ -n "$perms" ]]; then
            log_info "File permissions: $perms"
        fi
        
        return 0
    else
        log_warn "Testing mode is INACTIVE"
        log_info "To enable testing mode:"
        log_info "1. Add WAKE_WORD_TESTING_MODE=true to .env file"
        log_info "2. Restart StorytellerPi service"
        return 1
    fi
}

# Function to validate confidence value
validate_confidence() {
    local conf="$1"
    
    # Check if it's a valid number
    if ! [[ "$conf" =~ ^[0-9]*\.?[0-9]+$ ]]; then
        log_error "Invalid confidence value: $conf (must be a number)"
        return 1
    fi
    
    # Check if it's in valid range
    if (( $(echo "$conf < 0.0" | bc -l) )) || (( $(echo "$conf > 1.0" | bc -l) )); then
        log_error "Confidence must be between 0.0 and 1.0"
        return 1
    fi
    
    return 0
}

# Main function
main() {
    local confidence="1.0"
    local wake_word="hey_elsa"
    local verbose=false
    local quiet=false
    local command="trigger"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--confidence)
                confidence="$2"
                if ! validate_confidence "$confidence"; then
                    exit 1
                fi
                shift 2
                ;;
            -w|--word)
                wake_word="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            trigger)
                command="trigger"
                shift
                ;;
            trigger-custom)
                command="trigger-custom"
                wake_word="$2"
                shift 2
                ;;
            trigger-low)
                command="trigger"
                confidence="0.6"
                shift
                ;;
            trigger-high)
                command="trigger"
                confidence="0.95"
                shift
                ;;
            status)
                command="status"
                shift
                ;;
            help|--help|-h)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Set verbosity
    if [[ "$quiet" == "true" ]]; then
        verbose=false
    fi
    
    # Execute command
    case "$command" in
        trigger|trigger-custom)
            trigger_wake_word "$confidence" "$wake_word" "$verbose"
            ;;
        status)
            show_status
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Check if bc is available (for floating point comparison)
if ! command -v bc &> /dev/null; then
    log_warn "bc command not found - confidence validation may not work properly"
fi

# Run main function
main "$@"