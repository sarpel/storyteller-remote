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

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_validator import validate_configuration
from service_manager import initialize_services, ServiceManager
from audio_feedback import play_listening_started, play_listening_stopped, play_success_feedback, play_error_feedback


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
        
        # Service manager
        self.service_manager = None
        
        # Initialize application
        self._setup_logging()
        
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
    async def _initialize_services(self):
        """Initialize all service components with validation"""
        try:
            self.logger.info("Validating configuration...")
            
            # Validate configuration
            is_valid, validator = validate_configuration(self.env_file)
            if not is_valid:
                self.logger.error("Configuration validation failed")
                for error in validator.get_validation_errors():
                    self.logger.error(f"  - {error}")
                sys.exit(1)
            
            self.logger.info("Configuration validation passed")
            
            # Initialize service manager
            self.service_manager = await initialize_services(validator)
            
            # Set up wake word detection callback
            wake_word_service = self.service_manager.get_service('wake_word')
            if wake_word_service:
                wake_word_service.set_detection_callback(self._on_wake_word_detected)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            
            # Check if we can continue with degraded services
            if self.service_manager and self.service_manager.can_operate():
                self.logger.warning("Continuing with degraded services")
            else:
                self.logger.error("Critical services failed, cannot continue")
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
            
            # Check if TTS service is available
            tts_service = self.service_manager.get_service('tts')
            if tts_service and self.service_manager.is_service_available('tts'):
                await tts_service.speak_text("Hi! I'm listening!")
            
            # Check if STT service is available
            stt_service = self.service_manager.get_service('stt')
            if stt_service and self.service_manager.is_service_available('stt'):
                # Record audio for user input
                recording_duration = 5.0  # seconds
                self.logger.info(f"Recording audio for {recording_duration} seconds...")
                
                audio_data = stt_service.record_audio(recording_duration)
                
                if audio_data:
                    await self._process_user_input(audio_data)
                else:
                    self.logger.warning("No audio data recorded")
                    if tts_service:
                        await tts_service.speak_text("I didn't hear anything. Try again!")
            else:
                self.logger.error("STT service not available")
                if tts_service:
                    await tts_service.speak_text("Sorry, I can't hear you right now.")
                
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
            
            # Get services
            stt_service = self.service_manager.get_service('stt')
            llm_service = self.service_manager.get_service('llm')
            tts_service = self.service_manager.get_service('tts')
            
            # Speech-to-Text
            if stt_service and self.service_manager.is_service_available('stt'):
                self.logger.info("Processing speech-to-text...")
                user_text = await stt_service.transcribe_audio(audio_data)
                
                if not user_text:
                    if tts_service:
                        await tts_service.speak_text("I'm sorry, I couldn't understand what you said. Could you try again?")
                    return
                
                self.logger.info(f"User said: '{user_text}'")
            else:
                self.logger.error("STT service not available")
                if tts_service:
                    await tts_service.speak_text("Sorry, I can't understand speech right now.")
                return
            
            # Generate LLM response
            if llm_service and self.service_manager.is_service_available('llm'):
                self.logger.info("Generating response...")
                context_type = self._determine_context_type(user_text)
                response_text = await llm_service.generate_response(user_text, context_type)
                
                if not response_text:
                    if tts_service:
                        await tts_service.speak_text("I'm having trouble thinking of what to say. Let's try again!")
                    return
                
                self.logger.info(f"Generated response: '{response_text[:100]}...'")
            else:
                self.logger.error("LLM service not available")
                response_text = "I'm sorry, I can't think of a response right now."
            
            # Text-to-Speech
            await self._speak_response(response_text)
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            tts_service = self.service_manager.get_service('tts')
            if tts_service:
                await tts_service.speak_text("Oops! Something went wrong. Let's try again!")
    
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
            
            # Get TTS service
            tts_service = self.service_manager.get_service('tts')
            
            if tts_service and self.service_manager.is_service_available('tts'):
                # Split long responses into chunks if needed
                max_chunk_length = 200  # characters
                if len(response_text) <= max_chunk_length:
                    await tts_service.speak_text(response_text)
                else:
                    # Split into sentences and group them
                    sentences = response_text.split('. ')
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk + sentence) <= max_chunk_length:
                            current_chunk += sentence + ". "
                        else:
                            if current_chunk:
                                await tts_service.speak_text(current_chunk.strip())
                            current_chunk = sentence + ". "
                    
                    # Speak remaining chunk
                    if current_chunk:
                        await tts_service.speak_text(current_chunk.strip())
            else:
                self.logger.error("TTS service not available")
                # Log the response since we can't speak it
                self.logger.info(f"Response (TTS unavailable): {response_text}")
            
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
            
            # Initialize services
            await self._initialize_services()
            
            self.running = True
            
            # Test TTS on startup
            tts_service = self.service_manager.get_service('tts')
            if tts_service and self.service_manager.is_service_available('tts'):
                await tts_service.speak_text("Hello! I'm Elsa, your storytelling friend. Say 'Hey Elsa' to start!")
            
            # Start wake word detection
            wake_word_service = self.service_manager.get_service('wake_word')
            if wake_word_service and self.service_manager.is_service_available('wake_word'):
                wake_word_service.start_detection()
                self.logger.info("Wake word detection started")
            else:
                self.logger.warning("Wake word detection not available")
            
            self.logger.info("StorytellerPi is ready and listening...")
            
            # Main loop
            while self.running:
                await asyncio.sleep(1)
                
                # Check for error state
                if self.state == AppState.ERROR:
                    self.logger.error("Application in error state")
                    await asyncio.sleep(5)  # Wait before recovering
                    self._set_state(AppState.IDLE)
                
                # Periodic health check
                if hasattr(self, '_last_health_check'):
                    if asyncio.get_event_loop().time() - self._last_health_check > 300:  # 5 minutes
                        await self._perform_health_check()
                else:
                    self._last_health_check = asyncio.get_event_loop().time()
            
            self.logger.info("Shutting down StorytellerPi...")
            
        except Exception as e:
            self.logger.error(f"Critical error in main loop: {e}")
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Clean up service manager
            if self.service_manager:
                await self.service_manager.cleanup_services()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def _perform_health_check(self):
        """Perform periodic health check"""
        try:
            if self.service_manager:
                health_report = await self.service_manager.health_check()
                
                # Log degraded services
                if health_report['system_info']['degraded_services']:
                    self.logger.warning(f"Degraded services: {', '.join(health_report['system_info']['degraded_services'])}")
                
                # Log failed services
                if health_report['system_info']['failed_services']:
                    self.logger.error(f"Failed services: {', '.join(health_report['system_info']['failed_services'])}")
                
                # Check if we can still operate
                if not health_report['system_info']['can_operate']:
                    self.logger.error("Critical: System cannot operate with current service status")
                    self.running = False
                
                self._last_health_check = asyncio.get_event_loop().time()
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")


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
        logging.error(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the application
    exit_code = asyncio.run(main())
    sys.exit(exit_code)