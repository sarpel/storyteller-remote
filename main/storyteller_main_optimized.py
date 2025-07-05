"""
Optimized StorytellerPi Application for Pi Zero 2W
Memory and CPU optimized with lazy loading and conditional imports
"""

import os
import sys
import asyncio
import logging
import signal
import gc
from enum import Enum
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only essential modules at startup
from audio_feedback import play_listening_started, play_listening_stopped, play_success_feedback, play_error_feedback


class AppState(Enum):
    """Application state machine states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


class OptimizedStorytellerApp:
    """
    Memory-optimized StorytellerPi application for Pi Zero 2W
    Uses lazy loading and conditional imports to minimize RAM usage
    """
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.logger = None
        
        # Application state
        self.state = AppState.IDLE
        self.running = False
        
        # Service components (lazy loaded)
        self.wake_word_detector = None
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.audio_feedback = None
        
        # Memory optimization settings
        self.max_memory_usage = 400  # MB
        self.enable_memory_monitoring = True
        self.gc_frequency = 30  # seconds
        
        # Initialize application
        self._load_environment()
        self._setup_logging()
        self._check_system_resources()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start memory monitoring if enabled
        if self.enable_memory_monitoring:
            asyncio.create_task(self._memory_monitor())
    
    def _setup_logging(self):
        """Configure lightweight logging"""
        try:
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            
            # Configure logging with minimal overhead
            log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('logs/storyteller.log', mode='a'),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("Optimized logging initialized")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            sys.exit(1)
    
    def _load_environment(self):
        """Load environment variables with optimized defaults"""
        try:
            load_dotenv(self.env_file)
            
            # Set Pi Zero 2W optimized defaults
            os.environ.setdefault('LOG_LEVEL', 'WARNING')  # Reduce log verbosity
            os.environ.setdefault('INSTALL_DIR', '/opt/storytellerpi')
            os.environ.setdefault('LOG_DIR', '/opt/storytellerpi/logs')
            os.environ.setdefault('MODELS_DIR', '/opt/storytellerpi/models')
            os.environ.setdefault('TARGET_RESPONSE_TIME', '15.0')  # Relaxed for Pi Zero
            os.environ.setdefault('MAX_MEMORY_USAGE', '350')  # Conservative for Pi Zero
            os.environ.setdefault('WAKE_WORD_FRAMEWORK', 'porcupine')  # Most efficient
            os.environ.setdefault('WAKE_WORD_BUFFER_SIZE', '512')  # Smaller buffer
            os.environ.setdefault('ENABLE_MEMORY_MONITORING', 'true')
            os.environ.setdefault('GC_FREQUENCY', '30')
            
            # Update instance variables
            self.max_memory_usage = int(os.getenv('MAX_MEMORY_USAGE', '350'))
            self.enable_memory_monitoring = os.getenv('ENABLE_MEMORY_MONITORING', 'true').lower() == 'true'
            self.gc_frequency = int(os.getenv('GC_FREQUENCY', '30'))
            
            self.logger.info(f"Environment loaded with Pi Zero 2W optimizations")
            
        except Exception as e:
            print(f"Failed to load environment: {e}")
            print("Continuing with Pi Zero 2W defaults...")
    
    def _check_system_resources(self):
        """Check system resources and warn if insufficient"""
        try:
            import psutil
            
            # Check available memory
            memory = psutil.virtual_memory()
            available_mb = memory.available // (1024 * 1024)
            
            if available_mb < 200:
                self.logger.warning(f"Low memory: {available_mb}MB available")
                self.logger.warning("Consider closing other applications")
            
            # Check CPU
            cpu_count = psutil.cpu_count()
            if cpu_count < 4:
                self.logger.info(f"Running on {cpu_count} CPU cores - using conservative settings")
                
        except ImportError:
            self.logger.warning("psutil not available - cannot check system resources")
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
    
    def _lazy_load_wake_word_detector(self):
        """Lazy load wake word detector only when needed"""
        if self.wake_word_detector is None:
            try:
                self.logger.info("Loading wake word detector...")
                from wake_word_detector_optimized import WakeWordDetector
                self.wake_word_detector = WakeWordDetector()
                self.wake_word_detector.set_detection_callback(self._on_wake_word_detected)
                self.logger.info("Wake word detector loaded")
            except Exception as e:
                self.logger.error(f"Failed to load wake word detector: {e}")
                raise
        return self.wake_word_detector
    
    def _lazy_load_stt_service(self):
        """Lazy load STT service only when needed"""
        if self.stt_service is None:
            try:
                self.logger.info("Loading STT service...")
                from stt_service import STTService
                self.stt_service = STTService()
                self.logger.info("STT service loaded")
            except Exception as e:
                self.logger.error(f"Failed to load STT service: {e}")
                raise
        return self.stt_service
    
    def _lazy_load_llm_service(self):
        """Lazy load LLM service only when needed"""
        if self.llm_service is None:
            try:
                self.logger.info("Loading LLM service...")
                from storyteller_llm import StorytellerLLM
                self.llm_service = StorytellerLLM()
                self.logger.info("LLM service loaded")
            except Exception as e:
                self.logger.error(f"Failed to load LLM service: {e}")
                raise
        return self.llm_service
    
    def _lazy_load_tts_service(self):
        """Lazy load TTS service only when needed"""
        if self.tts_service is None:
            try:
                self.logger.info("Loading TTS service...")
                from tts_service import TTSService
                self.tts_service = TTSService()
                self.logger.info("TTS service loaded")
            except Exception as e:
                self.logger.error(f"Failed to load TTS service: {e}")
                raise
        return self.tts_service
    
    async def _memory_monitor(self):
        """Monitor memory usage and trigger garbage collection"""
        while self.running:
            try:
                import psutil
                
                memory = psutil.virtual_memory()
                used_mb = memory.used // (1024 * 1024)
                percent = memory.percent
                
                if used_mb > self.max_memory_usage or percent > 85:
                    self.logger.warning(f"High memory usage: {used_mb}MB ({percent}%)")
                    self.logger.info("Triggering garbage collection...")
                    
                    # Force garbage collection
                    collected = gc.collect()
                    self.logger.info(f"Garbage collection freed {collected} objects")
                    
                    # Check if we need to unload services
                    if percent > 90:
                        await self._emergency_memory_cleanup()
                
                await asyncio.sleep(self.gc_frequency)
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(60)  # Retry less frequently on error
    
    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup when running very low"""
        self.logger.warning("Emergency memory cleanup triggered")
        
        # Unload non-essential services
        if self.state == AppState.IDLE:
            if self.stt_service:
                del self.stt_service
                self.stt_service = None
                self.logger.info("STT service unloaded")
            
            if self.llm_service:
                del self.llm_service
                self.llm_service = None
                self.logger.info("LLM service unloaded")
            
            if self.tts_service:
                del self.tts_service
                self.tts_service = None
                self.logger.info("TTS service unloaded")
            
            # Force garbage collection
            gc.collect()
            self.logger.info("Emergency cleanup completed")
    
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
            self.state = AppState.LISTENING
            self.logger.info("Starting voice interaction")
            
            # Play listening feedback
            play_listening_started()
            
            # Lazy load STT service
            stt_service = self._lazy_load_stt_service()
            
            # Start listening for voice command
            audio_data = await stt_service.listen_for_speech()
            
            if audio_data:
                # Stop listening feedback
                play_listening_stopped()
                
                # Process the speech
                await self._process_speech(audio_data)
            else:
                self.logger.warning("No speech detected")
                play_error_feedback()
                self.state = AppState.IDLE
                
        except Exception as e:
            self.logger.error(f"Error handling wake word: {e}")
            play_error_feedback()
            self.state = AppState.ERROR
            await asyncio.sleep(5)  # Wait before returning to idle
            self.state = AppState.IDLE
    
    async def _process_speech(self, audio_data):
        """Process speech and generate response"""
        try:
            self.state = AppState.PROCESSING
            
            # Lazy load services
            stt_service = self._lazy_load_stt_service()
            llm_service = self._lazy_load_llm_service()
            tts_service = self._lazy_load_tts_service()
            
            # Convert speech to text
            self.logger.info("Converting speech to text...")
            text = await stt_service.transcribe_audio(audio_data)
            
            if not text:
                self.logger.warning("No text transcribed from speech")
                play_error_feedback()
                self.state = AppState.IDLE
                return
            
            self.logger.info(f"Transcribed text: {text}")
            
            # Generate story response
            self.logger.info("Generating story response...")
            story_response = await llm_service.generate_story(text)
            
            if not story_response:
                self.logger.warning("No story generated")
                play_error_feedback()
                self.state = AppState.IDLE
                return
            
            # Convert response to speech
            self.state = AppState.SPEAKING
            self.logger.info("Converting response to speech...")
            
            await tts_service.speak_text(story_response)
            
            # Play success feedback
            play_success_feedback()
            
            self.logger.info("Voice interaction completed successfully")
            self.state = AppState.IDLE
            
        except Exception as e:
            self.logger.error(f"Error processing speech: {e}")
            play_error_feedback()
            self.state = AppState.ERROR
            await asyncio.sleep(5)
            self.state = AppState.IDLE
    
    async def start(self):
        """Start the optimized StorytellerPi application"""
        try:
            self.logger.info("Starting optimized StorytellerPi application")
            self.running = True
            
            # Initialize only the wake word detector at startup
            wake_word_detector = self._lazy_load_wake_word_detector()
            
            # Start wake word detection
            if not wake_word_detector.start_detection():
                self.logger.error("Failed to start wake word detection")
                return False
            
            self.logger.info("StorytellerPi started successfully - listening for wake word")
            
            # Main application loop
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic garbage collection
                if hasattr(self, '_last_gc'):
                    if asyncio.get_event_loop().time() - self._last_gc > self.gc_frequency:
                        gc.collect()
                        self._last_gc = asyncio.get_event_loop().time()
                else:
                    self._last_gc = asyncio.get_event_loop().time()
            
            self.logger.info("Application loop ended")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in main application: {e}")
            return False
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Stop wake word detection
            if self.wake_word_detector:
                self.wake_word_detector.stop_detection()
                self.wake_word_detector.cleanup()
            
            # Clean up other services
            if self.stt_service:
                if hasattr(self.stt_service, 'cleanup'):
                    self.stt_service.cleanup()
            
            if self.llm_service:
                if hasattr(self.llm_service, 'cleanup'):
                    self.llm_service.cleanup()
            
            if self.tts_service:
                if hasattr(self.tts_service, 'cleanup'):
                    self.tts_service.cleanup()
            
            # Final garbage collection
            gc.collect()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point"""
    try:
        app = OptimizedStorytellerApp()
        await app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())