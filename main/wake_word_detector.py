"""
Wake Word Detection Module for StorytellerPi
Supports OpenWakeWord (ONNX/TFLite) and Porcupine (PPN) models
"""

import os
import time
import logging
import threading
import numpy as np
from typing import Optional, Callable
import pyaudio
from dotenv import load_dotenv

# Import audio feedback
from audio_feedback import play_wake_word_feedback

try:
    import openwakeword
    from openwakeword import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    logging.warning("OpenWakeWord not available")

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    logging.warning("Porcupine not available")

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available")


class WakeWordDetector:
    """
    Flexible wake word detector supporting multiple frameworks
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
        self.model_path = os.getenv('WAKE_WORD_MODEL_PATH', '/opt/storytellerpi/models/hey_elsa.onnx')
        self.threshold = float(os.getenv('WAKE_WORD_THRESHOLD', '0.5'))
        self.framework = os.getenv('WAKE_WORD_FRAMEWORK', 'openwakeword')
        
        # Porcupine specific settings
        self.porcupine_access_key = os.getenv('PORCUPINE_ACCESS_KEY')
        
        # Initialize components
        self.audio = None
        self.model = None
        self.stream = None
        self.detection_thread = None
        
        self._initialize_model()
        self._initialize_audio()
    
    def _initialize_model(self):
        """Initialize the wake word model based on framework"""
        try:
            if self.framework == "openwakeword" and OPENWAKEWORD_AVAILABLE:
                self._initialize_openwakeword()
            elif self.framework == "porcupine" and PORCUPINE_AVAILABLE:
                self._initialize_porcupine()
            elif self.framework == "tflite" and TENSORFLOW_AVAILABLE:
                self._initialize_tflite()
            else:
                raise ValueError(f"Framework {self.framework} not available or supported")
                
            self.logger.info(f"Wake word model initialized: {self.framework}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize wake word model: {e}")
            raise
    
    def _initialize_openwakeword(self):
        """Initialize OpenWakeWord model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # Initialize OpenWakeWord model
        self.model = Model(wakeword_models=[self.model_path])
        self.logger.info("OpenWakeWord model loaded successfully")    
    def _initialize_porcupine(self):
        """Initialize Porcupine model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # Requires Porcupine access key from environment
        if not self.porcupine_access_key:
            raise ValueError("PORCUPINE_ACCESS_KEY environment variable required for Porcupine")
        
        self.model = pvporcupine.create(
            access_key=self.porcupine_access_key,
            keyword_paths=[self.model_path]
        )
        self.logger.info(f"Porcupine model loaded successfully: {self.model_path}")
    
    def _initialize_tflite(self):
        """Initialize TensorFlow Lite model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
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
    
    def set_detection_callback(self, callback: Callable):
        """Set callback function to be called when wake word is detected"""
        self.detection_callback = callback
    
    def start_detection(self):
        """Start wake word detection in a separate thread"""
        if self.is_running:
            self.logger.warning("Detection already running")
            return
        
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        self.logger.info("Wake word detection started")
    
    def stop_detection(self):
        """Stop wake word detection"""
        self.is_running = False
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
        self.logger.info("Wake word detection stopped")    
    def _detection_loop(self):
        """Main detection loop running in separate thread"""
        self.logger.info("Starting wake word detection loop")
        
        try:
            while self.is_running:
                # Read audio chunk
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Process based on framework
                if self.framework == "openwakeword":
                    self._process_openwakeword(audio_array)
                elif self.framework == "porcupine":
                    self._process_porcupine(audio_array)
                elif self.framework == "tflite":
                    self._process_tflite(audio_array)
                    
        except Exception as e:
            self.logger.error(f"Error in detection loop: {e}")
        finally:
            self.logger.info("Detection loop ended")
    
    def _process_openwakeword(self, audio_data):
        """Process audio with OpenWakeWord"""
        # Get prediction scores
        prediction = self.model.predict(audio_data)
        
        # Check for wake word detection
        for wake_word, score in prediction.items():
            if score >= self.threshold:
                self.logger.info(f"Wake word '{wake_word}' detected with score: {score}")
                
                # Play audio feedback immediately
                try:
                    play_wake_word_feedback()
                except Exception as e:
                    self.logger.warning(f"Failed to play wake word feedback: {e}")
                
                if self.detection_callback:
                    self.detection_callback(wake_word, score)    
    def _process_porcupine(self, audio_data):
        """Process audio with Porcupine"""
        # Porcupine expects specific frame length
        frame_length = self.model.frame_length
        
        if len(audio_data) >= frame_length:
            # Process frame
            is_detected = self.model.process(audio_data[:frame_length])
            
            if is_detected >= 0:  # Wake word detected
                self.logger.info(f"Wake word detected by Porcupine")
                
                # Play audio feedback immediately
                try:
                    play_wake_word_feedback()
                except Exception as e:
                    self.logger.warning(f"Failed to play wake word feedback: {e}")
                
                if self.detection_callback:
                    self.detection_callback("hey_elsa", 1.0)
    
    def _process_tflite(self, audio_data):
        """Process audio with TensorFlow Lite"""
        # Prepare input data (this may need adjustment based on model requirements)
        input_data = audio_data.astype(np.float32) / 32768.0  # Normalize
        input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        # Get output
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        confidence = float(output_data[0])
        
        if confidence >= self.threshold:
            self.logger.info(f"Wake word detected with confidence: {confidence}")
            
            # Play audio feedback immediately
            try:
                play_wake_word_feedback()
            except Exception as e:
                self.logger.warning(f"Failed to play wake word feedback: {e}")
            
            if self.detection_callback:
                self.detection_callback("hey_elsa", confidence)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_detection()
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        if self.framework == "porcupine" and self.model:
            self.model.delete()
        
        self.logger.info("Wake word detector cleaned up")