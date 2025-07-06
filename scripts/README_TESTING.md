# StorytellerPi Wake Word Testing

This directory contains testing utilities for simulating wake word detection without actually saying the wake word. This is useful for development and testing on Raspberry Pi Zero 2W.

## ⚠️ IMPORTANT WARNING

**These testing features are for DEVELOPMENT ONLY and must be REMOVED in production!**

## Quick Start

### 1. Enable Testing Mode
```bash
# Enable testing mode
./scripts/setup_testing_mode.sh enable

# Restart the service
sudo systemctl restart storytellerpi
```

### 2. Test Wake Word Detection
```bash
# Simple trigger
./scripts/test_wake_word.sh

# Custom wake word
./scripts/test_wake_word.sh trigger-custom "hello"

# With specific confidence
./scripts/test_wake_word.sh -c 0.8

# Check status
./scripts/test_wake_word.sh status
```

### 3. Python Testing (Alternative)
```bash
# Simple trigger
python3 ./scripts/test_wake_word.py

# Interactive mode
python3 ./scripts/test_wake_word.py --interactive

# Batch testing
python3 ./scripts/test_wake_word.py --batch 5 --delay 3
```

### 4. Disable Testing Mode (Production)
```bash
./scripts/setup_testing_mode.sh disable
sudo systemctl restart storytellerpi
```

## Files

### `setup_testing_mode.sh`
- Enables/disables testing mode
- Updates .env configuration
- Shows current status

### `test_wake_word.sh`
- Bash script for triggering wake word detection
- Simple command-line interface
- Various trigger options

### `test_wake_word.py`
- Python script with more advanced features
- Interactive mode
- Batch testing capabilities

## How It Works

1. **Testing Mode**: When enabled, the wake word detector creates a FIFO pipe at `/tmp/storyteller_wake_trigger`
2. **Communication**: Test scripts write commands to this pipe
3. **Detection**: The wake word detector reads commands and simulates detection
4. **Feedback**: Audio feedback and callbacks work exactly as with real detection

## Configuration

Add to `.env` file:
```bash
# Testing Mode (REMOVE IN PRODUCTION!)
WAKE_WORD_TESTING_MODE=true
WAKE_WORD_TEST_TRIGGER_FILE=/tmp/storyteller_wake_trigger
```

## Testing Commands

The FIFO pipe accepts these commands:
- `WAKE` - Trigger with default settings
- `WAKE 0.8` - Trigger with specific confidence
- `WAKE 0.9 custom_word` - Trigger with confidence and custom wake word

## Usage Examples

### Basic Testing
```bash
# Enable testing
./scripts/setup_testing_mode.sh enable
sudo systemctl restart storytellerpi

# Test basic trigger
./scripts/test_wake_word.sh

# Test with low confidence
./scripts/test_wake_word.sh trigger-low

# Test with custom word
./scripts/test_wake_word.sh trigger-custom "hello storyteller"
```

### Advanced Testing
```bash
# Python interactive mode
python3 ./scripts/test_wake_word.py --interactive

# Commands in interactive mode:
# trigger              - Basic trigger
# custom hello         - Set custom wake word
# confidence 0.7       - Set confidence level
# status               - Check testing status
# quit                 - Exit

# Batch testing
python3 ./scripts/test_wake_word.py --batch 10 --delay 2
```

### Status Checking
```bash
# Check if testing mode is active
./scripts/setup_testing_mode.sh status
./scripts/test_wake_word.sh status
python3 ./scripts/test_wake_word.py --status
```

## Troubleshooting

### Testing Mode Not Active
1. Check if enabled in .env: `WAKE_WORD_TESTING_MODE=true`
2. Restart service: `sudo systemctl restart storytellerpi`
3. Check service status: `sudo systemctl status storytellerpi`

### Permission Issues
```bash
# Check trigger file permissions
ls -la /tmp/storyteller_wake_trigger

# If needed, fix permissions
sudo chmod 666 /tmp/storyteller_wake_trigger
```

### Service Not Running
```bash
# Check service status
sudo systemctl status storytellerpi

# Start service
sudo systemctl start storytellerpi

# Check logs
sudo journalctl -u storytellerpi -f
```

## Production Deployment

**Before deploying to production:**

1. **Disable testing mode**:
   ```bash
   ./scripts/setup_testing_mode.sh disable
   ```

2. **Remove testing files** (optional):
   ```bash
   rm -f ./scripts/test_wake_word.sh
   rm -f ./scripts/test_wake_word.py
   rm -f ./scripts/setup_testing_mode.sh
   rm -f ./scripts/README_TESTING.md
   ```

3. **Remove testing configuration from .env**:
   ```bash
   # Remove these lines:
   WAKE_WORD_TESTING_MODE=false
   WAKE_WORD_TEST_TRIGGER_FILE=/tmp/storyteller_wake_trigger
   ```

4. **Restart service**:
   ```bash
   sudo systemctl restart storytellerpi
   ```

## Security Notes

- Testing mode creates a world-writable FIFO pipe
- Any user can trigger wake word detection when testing is enabled
- This is a security risk in production environments
- Always disable testing mode before production deployment

## Integration with CI/CD

For automated testing:
```bash
# In your test pipeline
./scripts/setup_testing_mode.sh enable
sudo systemctl restart storytellerpi
sleep 5  # Wait for service to start

# Run tests
python3 ./scripts/test_wake_word.py --batch 3
./scripts/test_wake_word.sh status

# Cleanup
./scripts/setup_testing_mode.sh disable
```