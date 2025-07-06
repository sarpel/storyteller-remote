#!/bin/bash
# Setup StorytellerPi to work without hardware audio (software-only mode)
# Useful when HAT is not detected or USB audio not available

echo "🔇 Setting up StorytellerPi in No-Audio Mode"
echo "============================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run from StorytellerPi directory."
    exit 1
fi

echo "📝 Configuring StorytellerPi for software-only mode..."

# Update .env file for no-audio mode
cat >> .env << 'EOF'

# ============================================
# NO-AUDIO MODE CONFIGURATION
# ============================================

# Audio fallback mode (when no hardware audio detected)
AUDIO_FALLBACK_MODE=true
AUDIO_SOFTWARE_ONLY=true

# Disable hardware audio features
AUDIO_FEEDBACK_ENABLED=false
TTS_SERVICE=none
STT_PRIMARY_SERVICE=none

# Enable text-based interaction
WEB_ENABLED=true
WEB_PORT=8080
WEB_HOST=0.0.0.0

# Wake word alternatives
WAKE_WORD_FRAMEWORK=button
WAKE_WORD_BUTTON_GPIO=21

# Logging for debugging
LOG_LEVEL=INFO
ENABLE_TESTING=true

# Performance settings for Pi Zero 2W
MAX_MEMORY_USAGE=300
TARGET_RESPONSE_TIME=15.0

EOF

echo "✅ Updated .env file for no-audio mode"

# Create a simple web interface fallback
echo "🌐 Creating web interface for text interaction..."

mkdir -p web_fallback

cat > web_fallback/simple_interface.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>StorytellerPi - Text Mode</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
        .input-area { margin: 20px 0; }
        .output-area { background: white; padding: 15px; border-radius: 5px; min-height: 200px; border: 1px solid #ddd; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #45a049; }
        input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .status { color: #666; font-size: 0.9em; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 StorytellerPi - Text Mode</h1>
        <p class="status">Audio hardware not detected. Using text-based interaction.</p>
        
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type your message to Elsa..." />
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div class="output-area" id="output">
            <p><strong>Elsa:</strong> Hello! I'm Elsa, your storytelling friend. Since I can't hear you right now, you can type to me instead! What would you like to talk about?</p>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('userInput');
            const output = document.getElementById('output');
            const message = input.value.trim();
            
            if (message) {
                // Add user message
                output.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
                
                // Simulate response (in real implementation, this would call the LLM service)
                setTimeout(() => {
                    const responses = [
                        "That's a wonderful idea! Let me tell you a story about that...",
                        "How interesting! I love talking about that topic.",
                        "What a great question! Let me think about that...",
                        "That reminds me of a magical adventure story!",
                        "Tell me more about what you're thinking!"
                    ];
                    const response = responses[Math.floor(Math.random() * responses.length)];
                    output.innerHTML += `<p><strong>Elsa:</strong> ${response}</p>`;
                    output.scrollTop = output.scrollHeight;
                }, 1000);
                
                input.value = '';
                output.scrollTop = output.scrollHeight;
            }
        }
        
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
EOF

echo "✅ Created simple web interface"

# Create button wake word simulation
echo "🔘 Setting up GPIO button wake word simulation..."

cat > gpio_button_wakeword.py << 'EOF'
#!/usr/bin/env python3
"""
GPIO Button Wake Word simulation for StorytellerPi
When audio hardware is not available
"""

import RPi.GPIO as GPIO
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class ButtonWakeWord:
    """Button-based wake word detector for no-audio mode"""
    
    def __init__(self, button_pin: int = 21):
        self.button_pin = button_pin
        self.callback = None
        self.is_running = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        logger.info(f"Button wake word detector initialized on GPIO {self.button_pin}")
    
    def set_detection_callback(self, callback: Callable):
        """Set callback for button press detection"""
        self.callback = callback
    
    def start_detection(self):
        """Start button detection"""
        self.is_running = True
        
        # Add interrupt for button press
        GPIO.add_event_detect(
            self.button_pin, 
            GPIO.FALLING, 
            callback=self._button_pressed,
            bouncetime=300  # 300ms debounce
        )
        
        logger.info("Button wake word detection started")
    
    def stop_detection(self):
        """Stop button detection"""
        self.is_running = False
        GPIO.remove_event_detect(self.button_pin)
        logger.info("Button wake word detection stopped")
    
    def _button_pressed(self, channel):
        """Handle button press"""
        if self.callback and self.is_running:
            logger.info("Button pressed - wake word detected")
            self.callback("button_press", 1.0)
    
    def cleanup(self):
        """Clean up GPIO"""
        self.stop_detection()
        GPIO.cleanup()
        logger.info("Button wake word detector cleaned up")

if __name__ == "__main__":
    # Test button wake word detector
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(wake_word, confidence):
        print(f"Wake word detected: {wake_word} (confidence: {confidence})")
    
    detector = ButtonWakeWord()
    detector.set_detection_callback(test_callback)
    detector.start_detection()
    
    try:
        print("Press the button to test wake word detection...")
        print("Press Ctrl+C to exit")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.cleanup()
        print("Test completed")
EOF

chmod +x gpio_button_wakeword.py

echo "✅ Created GPIO button wake word detector"

# Create a startup script for no-audio mode
echo "🚀 Creating startup script for no-audio mode..."

cat > start_no_audio_mode.sh << 'EOF'
#!/bin/bash
# Start StorytellerPi in no-audio mode

echo "🔇 Starting StorytellerPi in No-Audio Mode"
echo "=========================================="

# Check if audio hardware is available
if aplay -l &>/dev/null && arecord -l &>/dev/null; then
    echo "⚠️  Audio hardware detected. Consider using normal mode."
    echo "   Continue anyway? (y/N)"
    read -n 1 response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 0
    fi
fi

echo "📋 No-audio mode features:"
echo "- GPIO button wake word (Pin 21)"
echo "- Web interface on port 8080"
echo "- Text-based interaction"
echo "- LED status indicators"

# Start web interface
echo "🌐 Starting web interface..."
cd web_fallback
python3 -m http.server 8080 &
WEB_PID=$!

echo "🔘 Starting GPIO button detection..."
python3 gpio_button_wakeword.py &
BUTTON_PID=$!

echo "🎭 Starting StorytellerPi main service..."
cd ..
python3 main/storyteller_main.py &
MAIN_PID=$!

echo ""
echo "✅ StorytellerPi started in no-audio mode!"
echo "   Web interface: http://$(hostname -I | awk '{print $1}'):8080"
echo "   GPIO button: Pin 21 (connect to ground to trigger)"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $WEB_PID $BUTTON_PID $MAIN_PID 2>/dev/null
    wait
    echo "Services stopped"
}

trap cleanup EXIT
wait
EOF

chmod +x start_no_audio_mode.sh

echo "✅ Created startup script"

echo ""
echo "🎯 No-Audio Mode Setup Complete!"
echo "=================================="
echo ""
echo "📝 Configuration updated in .env file"
echo "🌐 Web interface created in web_fallback/"
echo "🔘 GPIO button wake word on Pin 21"
echo "🚀 Startup script: ./start_no_audio_mode.sh"
echo ""
echo "💡 Usage:"
echo "1. Connect a button between GPIO 21 and Ground"
echo "2. Run: ./start_no_audio_mode.sh"
echo "3. Open web browser to: http://[pi-ip]:8080"
echo "4. Press button or use web interface to interact"
echo ""
echo "🔧 To return to normal audio mode later:"
echo "1. Fix audio hardware issues"
echo "2. Set AUDIO_SOFTWARE_ONLY=false in .env"
echo "3. Set AUDIO_FALLBACK_MODE=false in .env"
echo "4. Restart StorytellerPi"

echo ""
echo "📱 Hardware setup for button wake word:"
echo "   GPIO 21 ----[Button]---- Ground"
echo "   (Pin 40)              (Any ground pin)"