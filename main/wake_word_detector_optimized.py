"""
Optimized Wake Word Detection Module for Pi Zero 2W
Conditional imports and lazy loading to minimize RAM usage
"""

import os
import time
import logging
import threading
import pyaudio
from typing import Optional, Callable
from dotenv import load_dotenv

# Import audio feedback
from audio_feedback import play_wake_word_feedback


class WakeWordDetector:
    """
    Memory-optimized wake word detector for Pi Zero 2W
    Only loads the selected framework to minimize RAM usage
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.detection_callback = None
        
        # Audio configuration from environment
        self.sample_rate = int(os.getenv('WAKE_WORD_SAMPLE_RATE', '16000'))
        self.chunk_size = int(os.getenv('WAKE_WORD_BUFFER_SIZE', '1024'))
        self.channels = int(os.getenv('WAKE_WORD_CHANNELS', '1'))
        
        # Wake word configuration from environment
        self.model_path = os.getenv('WAKE_WORD_MODEL_PATH', '/opt/storytellerpi/models/hey_elsa.ppn')
        self.threshold = float(os.getenv('WAKE_WORD_THRESHOLD', '0.5'))
        self.framework = os.getenv('WAKE_WORD_FRAMEWORK', 'porcupine')
        
        # Porcupine specific settings
        self.porcupine_access_key = os.getenv('PORCUPINE_ACCESS_KEY')
        
        # Initialize components
        self.audio = None
        self.model = None
        self.stream = None
        self.detection_thread = None
        
        # Framework-specific attributes
        self._framework_module = None
        self._framework_available = False
        
        self._initialize_audio()
        self._check_framework_availability()
    
    def _check_framework_availability(self):
        """Check if the selected framework is available without importing"""
        try:
            if self.framework == "porcupine":
                import importlib.util
                spec = importlib.util.find_spec("pvporcupine")
                self._framework_available = spec is not None
            elif self.framework == "openwakeword":
                import importlib.util
                spec = importlib.util.find_spec("openwakeword")
                self._framework_available = spec is not None
            elif self.framework == "tflite":
                import importlib.util
                spec = importlib.util.find_spec("tflite_runtime")
                self._framework_available = spec is not None
            else:
                self._framework_available = False
                
            if not self._framework_available:
                self.logger.error(f"Framework {self.framework} not available")
                
        except Exception as e:
            self.logger.error(f"Error checking framework availability: {e}")
            self._framework_available = False
    
    def _lazy_load_framework(self):
        """Lazy load the selected framework only when needed"""
        if self._framework_module is not None:
            return True
            
        try:
            if self.framework == "porcupine" and self._framework_available:
                import pvporcupine
                self._framework_module = pvporcupine
                self._initialize_porcupine()
                return True
                
            elif self.framework == "openwakeword" and self._framework_available:
                import openwakeword
                from openwakeword import Model
                self._framework_module = openwakeword
                self._initialize_openwakeword()
                return True
                
            elif self.framework == "tflite" and self._framework_available:
                import tflite_runtime.interpreter as tflite
                self._framework_module = tflite
                self._initialize_tflite()
                return True
                
            else:
                self.logger.error(f"Framework {self.framework} not available for lazy loading")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to lazy load framework {self.framework}: {e}")
            return False
    
    def _initialize_porcupine(self):
        """Initialize Porcupine model (lazy loaded)"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        if not self.porcupine_access_key:
            raise ValueError("PORCUPINE_ACCESS_KEY environment variable required for Porcupine")
        
        self.model = self._framework_module.create(
            access_key=self.porcupine_access_key,
            keyword_paths=[self.model_path]
        )
        self.logger.info(f"Porcupine model loaded successfully: {self.model_path}")
    
    def _initialize_openwakeword(self):
        """Initialize OpenWakeWord model (lazy loaded)"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        from openwakeword import Model
        self.model = Model(wakeword_models=[self.model_path])
        self.logger.info("OpenWakeWord model loaded successfully")
    
    def _initialize_tflite(self):
        """Initialize TensorFlow Lite model (lazy loaded)"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        self.interpreter = self._framework_module.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.logger.info("TensorFlow Lite model loaded successfully")
    
    def _initialize_audio(self):
        """Initialize PyAudio for capturing audio"""
        self.audio = pyaudio.PyAudio()
        
        # Find input device
        device_index = None
        input_device = os.getenv('AUDIO_INPUT_DEVICE', 'default')
        if input_device != "default":
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if input_device in info['name']:
                    device_index = i
                    break
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            self.logger.info("Audio stream initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio stream: {e}")
            raise
    
    def set_detection_callback(self, callback: Callable[[str, float], None]):
        """Set callback function for wake word detection"""
        self.detection_callback = callback
    
    def start_detection(self):
        """Start wake word detection"""
        if not self._framework_available:
            self.logger.error("Cannot start detection - framework not available")
            return False
            
        if not self._lazy_load_framework():
            self.logger.error("Cannot start detection - failed to load framework")
            return False
            
        if self.is_running:
            self.logger.warning("Detection already running")
            return True
        
        try:
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            self.logger.info("Wake word detection started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start detection: {e}")
            self.is_running = False
            return False
    
    def stop_detection(self):
        """Stop wake word detection"""
        self.is_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        self.logger.info("Wake word detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        self.logger.info("Starting wake word detection loop")
        
        try:
            while self.is_running:
                # Read audio chunk
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Process based on framework
                if self.framework == "porcupine":
                    self._process_porcupine(audio_data)
                elif self.framework == "openwakeword":
                    self._process_openwakeword(audio_data)
                elif self.framework == "tflite":
                    self._process_tflite(audio_data)
                    
        except Exception as e:
            self.logger.error(f"Detection loop error: {e}")
        finally:
            self.logger.info("Detection loop ended")
    
    def _process_porcupine(self, audio_data):
        """Process audio with Porcupine"""
        import struct
        
        # Convert audio data to required format
        audio_frame = struct.unpack_from("h" * self.chunk_size, audio_data)
        
        # Process frame
        keyword_index = self.model.process(audio_frame)
        
        if keyword_index >= 0:
            wake_word = "hey_elsa"  # Default wake word name
            confidence = 1.0  # Porcupine doesn't provide confidence scores
            
            self.logger.info(f"Wake word detected: {wake_word}")
            
            # Play feedback
            play_wake_word_feedback()
            
            # Call detection callback
            if self.detection_callback:
                self.detection_callback(wake_word, confidence)
    
    def _process_openwakeword(self, audio_data):
        """Process audio with OpenWakeWord"""
        import numpy as np
        
        # Convert audio data to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Get predictions
        predictions = self.model.predict(audio_array)
        
        # Check for wake word detection
        for wake_word, confidence in predictions.items():
            if confidence > self.threshold:
                self.logger.info(f"Wake word detected: {wake_word} (confidence: {confidence})")
                
                # Play feedback
                play_wake_word_feedback()
                
                # Call detection callback
                if self.detection_callback:
                    self.detection_callback(wake_word, confidence)
    
    def _process_tflite(self, audio_data):
        """Process audio with TensorFlow Lite"""
        import numpy as np
        
        # Convert audio data to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Normalize audio
        audio_array = audio_array / 32768.0
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], audio_array)
        
        # Run inference
        self.interpreter.invoke()
        
        # Get output
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        confidence = float(output_data[0])
        
        if confidence > self.threshold:
            wake_word = "hey_elsa"  # Default wake word name
            
            self.logger.info(f"Wake word detected: {wake_word} (confidence: {confidence})")
            
            # Play feedback
            play_wake_word_feedback()
            
            # Call detection callback
            if self.detection_callback:
                self.detection_callback(wake_word, confidence)
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_detection()
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            if self.audio:
                self.audio.terminate()
            
            if self.model and hasattr(self.model, 'delete'):
                self.model.delete()
                
            self.logger.info("Wake word detector cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")