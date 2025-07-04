"""
Main StorytellerPi Application
Voice-activated storytelling device for children using Raspberry Pi Zero 2W
"""

import os
import sys
import asyncio
import logging
import signal
from enum import Enum
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wake_word_detector import WakeWordDetector
from stt_service import STTService
from storyteller_llm import StorytellerLLM
from tts_service import TTSService
from audio_feedback import get_audio_feedback, play_listening_started, play_listening_stopped, play_success_feedback, play_error_feedback


class AppState(Enum):
    """Application state machine states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


class StorytellerApp:
    """
    Main application class for StorytellerPi
    """
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.logger = None
        
        # Application state
        self.state = AppState.IDLE
        self.running = False
        
        # Service components
        self.wake_word_detector = None
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        
        # Initialize application
        self._load_environment()
        self._setup_logging()
        self._initialize_services()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Configure logging"""
        try:
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('logs/storyteller.log'),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("Logging initialized")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            sys.exit(1)    
    def _load_environment(self):
        """Load environment variables from .env file"""
        try:
            # Load .env file
            load_dotenv(self.env_file)
            
            # Set default values if not specified
            os.environ.setdefault('LOG_LEVEL', 'INFO')
            os.environ.setdefault('INSTALL_DIR', '/opt/storytellerpi')
            os.environ.setdefault('LOG_DIR', '/opt/storytellerpi/logs')
            os.environ.setdefault('MODELS_DIR', '/opt/storytellerpi/models')
            os.environ.setdefault('TARGET_RESPONSE_TIME', '11.0')
            os.environ.setdefault('MAX_MEMORY_USAGE', '400')
            
            print(f"Environment loaded from {self.env_file}")
            
        except Exception as e:
            print(f"Failed to load environment: {e}")
            print("Continuing with default settings...")
            
            # Set basic defaults
            os.environ.setdefault('LOG_LEVEL', 'INFO')
            os.environ.setdefault('INSTALL_DIR', '/opt/storytellerpi')
            os.environ.setdefault('LOG_DIR', '/opt/storytellerpi/logs')
    
    def _initialize_services(self):
        """Initialize all service components"""
        try:
            self.logger.info("Initializing services...")
            
            # Initialize wake word detector
            self.wake_word_detector = WakeWordDetector()
            self.wake_word_detector.set_detection_callback(self._on_wake_word_detected)
            
            # Initialize STT service
            self.stt_service = STTService()
            
            # Initialize LLM service
            self.llm_service = StorytellerLLM()
            
            # Initialize TTS service
            self.tts_service = TTSService()
            
            # Initialize audio feedback
            self.audio_feedback = get_audio_feedback()
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _on_wake_word_detected(self, wake_word: str, confidence: float):
        """Callback for wake word detection"""
        if self.state == AppState.IDLE:
            self.logger.info(f"Wake word detected: {wake_word} (confidence: {confidence})")
            asyncio.create_task(self._handle_wake_word())
    
    async def _handle_wake_word(self):
        """Handle wake word detection and start listening"""
        try:
            self._set_state(AppState.LISTENING)
            
            # Play listening started feedback (already played by wake word detector)
            # Just give verbal feedback
            await self.tts_service.speak_text("Hi! I'm listening!")
            
            # Record audio for user input
            recording_duration = 5.0  # seconds
            self.logger.info(f"Recording audio for {recording_duration} seconds...")
            
            audio_data = self.stt_service.record_audio(recording_duration)
            
            if audio_data:
                await self._process_user_input(audio_data)
            else:
                self.logger.warning("No audio data recorded")
                await self.tts_service.speak_text("I didn't hear anything. Try again!")
                
        except Exception as e:
            self.logger.error(f"Error handling wake word: {e}")
            self._set_state(AppState.ERROR)
            # Play error feedback
            try:
                play_error_feedback()
            except Exception as e:
                self.logger.warning(f"Failed to play error feedback: {e}")
        finally:
            self._set_state(AppState.IDLE)
            # Play listening stopped feedback
            try:
                play_listening_stopped()
            except Exception as e:
                self.logger.warning(f"Failed to play listening stopped feedback: {e}")    
    async def _process_user_input(self, audio_data: bytes):
        """Process user audio input through STT and LLM"""
        try:
            self._set_state(AppState.PROCESSING)
            
            # Speech-to-Text
            self.logger.info("Processing speech-to-text...")
            user_text = await self.stt_service.transcribe_audio(audio_data)
            
            if not user_text:
                await self.tts_service.speak_text("I'm sorry, I couldn't understand what you said. Could you try again?")
                return
            
            self.logger.info(f"User said: '{user_text}'")
            
            # Determine context type
            context_type = self._determine_context_type(user_text)
            
            # Generate LLM response
            self.logger.info("Generating response...")
            response_text = await self.llm_service.generate_response(user_text, context_type)
            
            if not response_text:
                await self.tts_service.speak_text("I'm having trouble thinking of what to say. Let's try again!")
                return
            
            self.logger.info(f"Generated response: '{response_text[:100]}...'")
            
            # Text-to-Speech
            await self._speak_response(response_text)
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            await self.tts_service.speak_text("Oops! Something went wrong. Let's try again!")
    
    def _determine_context_type(self, user_text: str) -> str:
        """Determine the type of user request"""
        text_lower = user_text.lower()
        
        # Story request keywords
        story_keywords = ["story", "tale", "tell me about", "once upon", "adventure"]
        if any(keyword in text_lower for keyword in story_keywords):
            return "story_request"
        
        # Question keywords
        question_keywords = ["what", "why", "how", "when", "where", "who", "?"]
        if any(keyword in text_lower for keyword in question_keywords):
            return "question"
        
        # Default to conversation
        return "conversation"
    
    async def _speak_response(self, response_text: str):
        """Convert response to speech and play it"""
        try:
            self._set_state(AppState.SPEAKING)
            
            # Split long responses into chunks if needed
            max_chunk_length = 200  # characters
            if len(response_text) <= max_chunk_length:
                await self.tts_service.speak_text(response_text)
            else:
                # Split into sentences and group them
                sentences = response_text.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) <= max_chunk_length:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            await self.tts_service.speak_text(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                # Speak remaining chunk
                if current_chunk:
                    await self.tts_service.speak_text(current_chunk.strip())
            
            # Play success feedback after speaking
            try:
                play_success_feedback()
            except Exception as e:
                self.logger.warning(f"Failed to play success feedback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error speaking response: {e}")    
    def _set_state(self, new_state: AppState):
        """Update application state"""
        if self.state != new_state:
            self.logger.info(f"State change: {self.state.value} -> {new_state.value}")
            self.state = new_state
    
    async def run(self):
        """Main application loop"""
        try:
            self.logger.info("Starting StorytellerPi...")
            self.running = True
            
            # Test TTS on startup
            await self.tts_service.speak_text("Hello! I'm Elsa, your storytelling friend. Say 'Hey Elsa' to start!")
            
            # Start wake word detection
            self.wake_word_detector.start_detection()
            
            self.logger.info("StorytellerPi is ready and listening...")
            
            # Main loop
            while self.running:
                await asyncio.sleep(1)
                
                # Check for error state
                if self.state == AppState.ERROR:
                    self.logger.error("Application in error state")
                    await asyncio.sleep(5)  # Wait before recovering
                    self._set_state(AppState.IDLE)
            
            self.logger.info("Shutting down StorytellerPi...")
            
        except Exception as e:
            self.logger.error(f"Critical error in main loop: {e}")
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Stop wake word detection
            if self.wake_word_detector:
                self.wake_word_detector.cleanup()
            
            # Stop TTS playback
            if self.tts_service:
                self.tts_service.cleanup()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point"""
    try:
        # Change to script directory
        script_dir = Path(__file__).parent.parent
        os.chdir(script_dir)
        
        # Create and run application
        app = StorytellerApp()
        await app.run()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the application
    exit_code = asyncio.run(main())
    sys.exit(exit_code)