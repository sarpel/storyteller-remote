#!/usr/bin/env python3
"""
Configuration Validator for StorytellerPi
Validates environment variables and provides fallback values
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates and manages configuration settings"""
    
    # Required environment variables that must be set
    REQUIRED_VARS = [
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY', 
        'ELEVENLABS_VOICE_ID',
        'PORCUPINE_ACCESS_KEY'
    ]
    
    # Optional variables with fallback values
    OPTIONAL_VARS = {
        # Hardware Configuration
        'HARDWARE_MODEL': 'unknown',
        'OPERATING_SYSTEM': 'unknown',
        'AUDIO_DEVICE': 'default',
        'AUDIO_ENABLED': 'true',
        'AUDIO_DRIVER': 'alsa',
        'AUDIO_SYSTEM': 'alsa',
        'AUDIO_DEVICE_NAME': 'Default Audio Device',
        'AUDIO_MIXER_CONTROL': 'Master',
        'AUDIO_PULSE_SERVER': '',
        
        # Audio Settings
        'AUDIO_SAMPLE_RATE': '16000',
        'AUDIO_CHANNELS': '1',
        'AUDIO_CHUNK_SIZE': '1024',
        'AUDIO_INPUT_DEVICE': 'default',
        'AUDIO_OUTPUT_DEVICE': 'default',
        
        # Turkish Language Settings
        'SYSTEM_LANGUAGE': 'tr-TR',
        'SYSTEM_LOCALE': 'tr_TR.UTF-8',
        'STORY_LANGUAGE': 'turkish',
        'CHILD_NAME': 'Küçük Prenses',
        'CHILD_AGE': '5',
        'CHILD_GENDER': 'kız',
        
        # Wake Word Settings (Turkish)
        'WAKE_WORD': 'merhaba asistan',
        'WAKE_WORD_FRAMEWORK': 'porcupine',
        'WAKE_WORD_SENSITIVITY': '0.7',
        'WAKE_WORD_MODEL_PATH': '/opt/storytellerpi/models/merhaba-asistan.ppn',
        
        # STT Settings (Remote Only - Turkish)
        'STT_SERVICE': 'google',
        'STT_LANGUAGE_CODE': 'tr-TR',
        'STT_ALTERNATIVE_LANGUAGE': 'tr',
        'STT_TIMEOUT': '10.0',
        'STT_MAX_AUDIO_LENGTH': '30.0',
        'STT_USE_LOCAL_MODELS': 'false',
        'STT_REMOTE_ONLY': 'true',
        
        # LLM Settings (Remote Only - Turkish)
        'LLM_SERVICE': 'openai',
        'LLM_MODEL': 'gpt-4',
        'LLM_LANGUAGE': 'turkish',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '1000',
        'LLM_CONVERSATION_HISTORY_LIMIT': '10',
        'LLM_CHILD_SAFE_MODE': 'true',
        'LLM_AGE_APPROPRIATE_CONTENT': '5',
        'LLM_CONTENT_FILTER_LEVEL': 'strict',
        
        # TTS Settings (Remote Only - Turkish)
        'TTS_SERVICE': 'elevenlabs',
        'TTS_LANGUAGE': 'tr',
        'TTS_VOICE_GENDER': 'female',
        'TTS_VOICE_AGE': 'young_adult',
        'TTS_VOICE_STYLE': 'storyteller',
        'TTS_VOICE_STABILITY': '0.8',
        'TTS_VOICE_SIMILARITY_BOOST': '0.7',
        'TTS_MODEL_ID': 'eleven_turbo_v2',
        'TTS_REMOTE_ONLY': 'true',
        
        # Child-Specific Story Configuration
        'STORY_TARGET_AUDIENCE': '5_year_old_girl',
        'STORY_CONTENT_FILTER': 'very_strict',
        'STORY_THEMES': 'prenses,peri,dostluk,macera,hayvanlar',
        'STORY_LENGTH': 'short',
        'STORY_TONE': 'gentle_enthusiastic',
        'STORY_INCLUDE_MORAL': 'true',
        'STORY_AVOID_SCARY': 'true',
        'STORY_GREETING': 'Merhaba küçük prenses! Bugün sana güzel bir hikaye anlatmak istiyorum.',
        
        # System Settings (Pi Zero 2W Optimized)
        'INSTALL_DIR': '/opt/storytellerpi',
        'LOG_DIR': '/opt/storytellerpi/logs',
        'MODELS_DIR': '/opt/storytellerpi/models',
        'CREDENTIALS_DIR': '/opt/storytellerpi/credentials',
        'LOG_LEVEL': 'INFO',
        'LOG_LANGUAGE': 'turkish',
        'SERVICE_NAME': 'storytellerpi',
        'MAX_MEMORY_USAGE': '300',
        'TARGET_RESPONSE_TIME': '8.0',
        
        # Performance Optimization for Pi Zero 2W
        'OPTIMIZE_FOR_PI_ZERO': 'true',
        'USE_LOCAL_MODELS': 'false',
        'MEMORY_LIMIT': '300',
        'CPU_LIMIT': '80',
        'DISABLE_HEAVY_PROCESSING': 'true',
        
        # Web Interface (Turkish)
        'WEB_ENABLED': 'true',
        'WEB_LANGUAGE': 'tr',
        'WEB_TITLE': 'Hikaye Asistanı',
        'WEB_HOST': '0.0.0.0',
        'WEB_PORT': '5000',
        'WEB_DEBUG': 'false',
        'WEB_SECRET_KEY': 'hikaye-asistani-secret-key',
        
        # Audio Feedback
        'AUDIO_FEEDBACK_ENABLED': 'true',
        'AUDIO_FEEDBACK_VOLUME': '0.3',
        'AUDIO_FEEDBACK_WAKE_WORD_TONE': '880.0',
        'AUDIO_FEEDBACK_WAKE_WORD_DURATION': '0.3',
        'AUDIO_FALLBACK_MODE': 'false',
        'AUDIO_SOFTWARE_ONLY': 'false',
        
        # Performance
        'ENABLE_MEMORY_MONITORING': 'true',
        'MEMORY_CHECK_INTERVAL': '30.0',
        'CPU_CHECK_INTERVAL': '10.0',
        'HEALTH_CHECK_ENABLED': 'true',
        'HEALTH_CHECK_INTERVAL': '300.0'
    }
    
    # Conditional requirements based on service choices (Remote Only)
    CONDITIONAL_REQUIREMENTS = {
        'turkish_storyteller': ['OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID', 'PORCUPINE_ACCESS_KEY'],
        'google_stt': ['GOOGLE_APPLICATION_CREDENTIALS'],
        'elevenlabs_tts': ['ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID'],
        'openai_llm': ['OPENAI_API_KEY'],
        'porcupine_wake_word': ['PORCUPINE_ACCESS_KEY']
    }
    
    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file
        self.validation_errors = []
        self.warnings = []
        self.config = {}
        
    def load_and_validate(self) -> bool:
        """Load environment variables and validate configuration"""
        try:
            # Load .env file
            if os.path.exists(self.env_file):
                load_dotenv(self.env_file)
                logger.info(f"Loaded environment from {self.env_file}")
            else:
                logger.warning(f"Environment file {self.env_file} not found")
            
            # Validate required variables
            self._validate_required_vars()
            
            # Set fallback values for optional variables
            self._set_fallback_values()
            
            # Validate conditional requirements
            self._validate_conditional_requirements()
            
            # Validate file paths
            self._validate_file_paths()
            
            # Validate numeric values
            self._validate_numeric_values()
            
            # Store final configuration
            self._store_configuration()
            
            # Report validation results
            self._report_validation_results()
            
            return len(self.validation_errors) == 0
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _validate_required_vars(self):
        """Validate required environment variables"""
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                self.validation_errors.append(f"Required environment variable '{var}' is not set")
            elif var.endswith('_KEY') and len(value) < 10:
                self.validation_errors.append(f"Environment variable '{var}' appears to be invalid (too short)")
    
    def _set_fallback_values(self):
        """Set fallback values for optional variables"""
        for var, fallback in self.OPTIONAL_VARS.items():
            if not os.getenv(var):
                os.environ[var] = fallback
                logger.debug(f"Set fallback value for {var}: {fallback}")
    
    def _validate_conditional_requirements(self):
        """Validate conditional requirements based on service choices"""
        # Check Google STT requirements
        if os.getenv('STT_PRIMARY_SERVICE') == 'google':
            for var in self.CONDITIONAL_REQUIREMENTS['google_stt']:
                if not os.getenv(var):
                    self.validation_errors.append(f"Required for Google STT: '{var}' is not set")
        
        # Check OpenAI fallback requirements
        if os.getenv('STT_FALLBACK_SERVICE') == 'openai':
            for var in self.CONDITIONAL_REQUIREMENTS['openai_fallback']:
                if not os.getenv(var):
                    self.warnings.append(f"OpenAI fallback enabled but '{var}' is not set")
        
        # Check ElevenLabs TTS requirements
        if os.getenv('TTS_SERVICE') == 'elevenlabs':
            for var in self.CONDITIONAL_REQUIREMENTS['elevenlabs_tts']:
                if not os.getenv(var):
                    self.validation_errors.append(f"Required for ElevenLabs TTS: '{var}' is not set")
        
        # Check Porcupine wake word requirements
        if os.getenv('WAKE_WORD_FRAMEWORK') == 'porcupine':
            for var in self.CONDITIONAL_REQUIREMENTS['porcupine_wake_word']:
                if not os.getenv(var):
                    self.validation_errors.append(f"Required for Porcupine wake word: '{var}' is not set")
    
    def _validate_file_paths(self):
        """Validate file paths exist"""
        path_vars = [
            'WAKE_WORD_MODEL_PATH',
            'GOOGLE_CREDENTIALS_JSON'
        ]
        
        for var in path_vars:
            path = os.getenv(var)
            if path and not os.path.exists(path):
                self.validation_errors.append(f"File path '{var}' does not exist: {path}")
    
    def _validate_numeric_values(self):
        """Validate numeric environment variables"""
        numeric_vars = {
            'AUDIO_SAMPLE_RATE': (8000, 48000),
            'AUDIO_CHANNELS': (1, 2),
            'AUDIO_CHUNK_SIZE': (512, 8192),
            'WAKE_WORD_THRESHOLD': (0.1, 1.0),
            'LLM_TEMPERATURE': (0.0, 2.0),
            'LLM_MAX_TOKENS': (100, 4000),
            'TTS_VOICE_STABILITY': (0.0, 1.0),
            'TTS_VOICE_SIMILARITY_BOOST': (0.0, 1.0),
            'WEB_PORT': (1000, 65535),
            'AUDIO_FEEDBACK_VOLUME': (0.0, 1.0)
        }
        
        for var, (min_val, max_val) in numeric_vars.items():
            value = os.getenv(var)
            if value:
                try:
                    num_val = float(value)
                    if not (min_val <= num_val <= max_val):
                        self.warnings.append(f"'{var}' value {num_val} is outside recommended range ({min_val}-{max_val})")
                except ValueError:
                    self.validation_errors.append(f"'{var}' must be a numeric value, got: {value}")
    
    def _store_configuration(self):
        """Store final configuration for easy access"""
        self.config = {
            'audio': {
                'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE')),
                'channels': int(os.getenv('AUDIO_CHANNELS')),
                'chunk_size': int(os.getenv('AUDIO_CHUNK_SIZE')),
                'input_device': os.getenv('AUDIO_INPUT_DEVICE'),
                'output_device': os.getenv('AUDIO_OUTPUT_DEVICE')
            },
            'wake_word': {
                'framework': os.getenv('WAKE_WORD_FRAMEWORK'),
                'model_path': os.getenv('WAKE_WORD_MODEL_PATH'),
                'threshold': float(os.getenv('WAKE_WORD_THRESHOLD')),
                'sample_rate': int(os.getenv('WAKE_WORD_SAMPLE_RATE')),
                'buffer_size': int(os.getenv('WAKE_WORD_BUFFER_SIZE'))
            },
            'stt': {
                'primary_service': os.getenv('STT_PRIMARY_SERVICE'),
                'language_code': os.getenv('STT_LANGUAGE_CODE'),
                'timeout': float(os.getenv('STT_TIMEOUT')),
                'max_audio_length': float(os.getenv('STT_MAX_AUDIO_LENGTH'))
            },
            'llm': {
                'service': os.getenv('LLM_SERVICE'),
                'model': os.getenv('LLM_MODEL'),
                'temperature': float(os.getenv('LLM_TEMPERATURE')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS')),
                'child_safe_mode': os.getenv('LLM_CHILD_SAFE_MODE').lower() == 'true'
            },
            'tts': {
                'service': os.getenv('TTS_SERVICE'),
                'voice_stability': float(os.getenv('TTS_VOICE_STABILITY')),
                'voice_similarity_boost': float(os.getenv('TTS_VOICE_SIMILARITY_BOOST'))
            },
            'system': {
                'install_dir': os.getenv('INSTALL_DIR'),
                'log_dir': os.getenv('LOG_DIR'),
                'models_dir': os.getenv('MODELS_DIR'),
                'log_level': os.getenv('LOG_LEVEL'),
                'service_name': os.getenv('SERVICE_NAME')
            }
        }
    
    def _report_validation_results(self):
        """Report validation results"""
        if self.validation_errors:
            logger.error("Configuration validation failed:")
            for error in self.validation_errors:
                logger.error(f"  ❌ {error}")
        
        if self.warnings:
            logger.warning("Configuration warnings:")
            for warning in self.warnings:
                logger.warning(f"  ⚠️  {warning}")
        
        if not self.validation_errors and not self.warnings:
            logger.info("✅ Configuration validation passed")
    
    def get_config(self) -> Dict[str, Any]:
        """Get validated configuration"""
        return self.config
    
    def get_validation_errors(self) -> List[str]:
        """Get validation errors"""
        return self.validation_errors
    
    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return len(self.validation_errors) == 0
    
    def create_directories(self) -> bool:
        """Create required directories"""
        try:
            directories = [
                os.getenv('LOG_DIR'),
                os.getenv('MODELS_DIR'),
                os.getenv('INSTALL_DIR')
            ]
            
            for directory in directories:
                if directory:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Ensured directory exists: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False


def validate_configuration(env_file: str = '.env') -> tuple[bool, ConfigValidator]:
    """
    Validate configuration and return results
    
    Returns:
        tuple: (is_valid, validator_instance)
    """
    validator = ConfigValidator(env_file)
    is_valid = validator.load_and_validate()
    
    if is_valid:
        validator.create_directories()
    
    return is_valid, validator


if __name__ == "__main__":
    # Test configuration validation
    import sys
    
    # Ensure UTF-8 encoding for console output
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    logging.basicConfig(level=logging.INFO)
    
    is_valid, validator = validate_configuration()
    
    if is_valid:
        print("Configuration is valid!")
        print(f"Configuration loaded: {len(validator.get_config())} sections")
    else:
        print("Configuration validation failed!")
        for error in validator.get_validation_errors():
            print(f"  - {error}")
        exit(1)