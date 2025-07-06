#!/usr/bin/env python3
"""
Integration tests for StorytellerPi services
Tests service interactions and graceful degradation
"""

import os
import sys
import pytest
import asyncio
import tempfile
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

# Set up test environment
os.environ['GEMINI_API_KEY'] = 'test_key'
os.environ['WAKE_WORD_MODEL_PATH'] = '/tmp/test_model.onnx'
os.environ['WAKE_WORD_FRAMEWORK'] = 'openwakeword'

from config_validator import ConfigValidator
from service_manager import ServiceManager, ServiceStatus
from storyteller_main import StorytellerApp


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_configuration(self):
        """Test valid configuration passes validation"""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("GEMINI_API_KEY=test_key\n")
            f.write("WAKE_WORD_MODEL_PATH=/tmp/test_model.onnx\n")
            f.write("WAKE_WORD_FRAMEWORK=openwakeword\n")
            temp_env_file = f.name
        
        try:
            # Create test model file
            test_model_path = Path(tempfile.gettempdir()) / 'test_model.onnx'
            test_model_path.touch()
            
            # Update environment variable to use the correct path
            os.environ['WAKE_WORD_MODEL_PATH'] = str(test_model_path)
            
            validator = ConfigValidator(temp_env_file)
            is_valid = validator.load_and_validate()
            
            assert is_valid, f"Configuration should be valid. Errors: {validator.get_validation_errors()}"
            
        finally:
            # Clean up
            os.unlink(temp_env_file)
            test_model_path = Path(tempfile.gettempdir()) / 'test_model.onnx'
            if test_model_path.exists():
                test_model_path.unlink()
    
    def test_missing_required_vars(self):
        """Test missing required variables fails validation"""
        # Create temporary .env file without required variables
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("AUDIO_SAMPLE_RATE=16000\n")
            temp_env_file = f.name
        
        try:
            validator = ConfigValidator(temp_env_file)
            is_valid = validator.load_and_validate()
            
            assert not is_valid, "Configuration should be invalid"
            assert len(validator.get_validation_errors()) > 0
            
        finally:
            os.unlink(temp_env_file)
    
    def test_fallback_values(self):
        """Test fallback values are set correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("GEMINI_API_KEY=test_key\n")
            f.write("WAKE_WORD_MODEL_PATH=/tmp/test_model.onnx\n")
            f.write("WAKE_WORD_FRAMEWORK=openwakeword\n")
            temp_env_file = f.name
        
        try:
            test_model_path = Path(tempfile.gettempdir()) / 'test_model.onnx'
            test_model_path.touch()
            
            # Update environment variable to use the correct path
            os.environ['WAKE_WORD_MODEL_PATH'] = str(test_model_path)
            
            validator = ConfigValidator(temp_env_file)
            validator.load_and_validate()
            
            # Check that fallback values are set
            assert os.getenv('AUDIO_SAMPLE_RATE') == '16000'
            assert os.getenv('AUDIO_CHANNELS') == '1'
            assert os.getenv('LOG_LEVEL') == 'INFO'
            
        finally:
            os.unlink(temp_env_file)
            test_model_path = Path(tempfile.gettempdir()) / 'test_model.onnx'
            if test_model_path.exists():
                test_model_path.unlink()


class TestServiceManager:
    """Test service manager functionality"""
    
    @pytest.fixture
    def mock_config_validator(self):
        """Create mock config validator"""
        validator = Mock(spec=ConfigValidator)
        validator.get_config.return_value = {
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'chunk_size': 1024,
                'input_device': 'default',
                'output_device': 'default'
            },
            'wake_word': {
                'framework': 'openwakeword',
                'model_path': '/tmp/test_model.onnx',
                'threshold': 0.5,
                'sample_rate': 16000,
                'buffer_size': 1024
            },
            'stt': {
                'primary_service': 'google',
                'language_code': 'en-US',
                'timeout': 30.0,
                'max_audio_length': 60.0
            },
            'llm': {
                'service': 'gemini',
                'model': 'gemini-2.5-flash',
                'temperature': 0.7,
                'max_tokens': 1000,
                'child_safe_mode': True
            },
            'tts': {
                'service': 'elevenlabs',
                'voice_stability': 0.75,
                'voice_similarity_boost': 0.75
            },
            'system': {
                'install_dir': '/opt/storytellerpi',
                'log_dir': '/opt/storytellerpi/logs',
                'models_dir': '/opt/storytellerpi/models',
                'log_level': 'INFO',
                'service_name': 'storytellerpi'
            }
        }
        return validator
    
    @pytest.mark.asyncio
    async def test_service_manager_initialization(self, mock_config_validator):
        """Test service manager initialization"""
        with patch('wake_word_detector.WakeWordDetector') as mock_wake_word:
            with patch('stt_service.STTService') as mock_stt:
                with patch('storyteller_llm.StorytellerLLM') as mock_llm:
                    with patch('tts_service.TTSService') as mock_tts:
                        with patch('audio_feedback.get_audio_feedback') as mock_audio:
                            
                            mock_wake_word.return_value = Mock()
                            mock_stt.return_value = Mock()
                            mock_llm.return_value = Mock()
                            mock_tts.return_value = Mock()
                            mock_audio.return_value = Mock()
                            
                            service_manager = ServiceManager(mock_config_validator)
                            success = await service_manager.initialize_all_services()
                            
                            assert success
                            assert service_manager.can_operate()
                            assert service_manager.get_service('wake_word') is not None
                            assert service_manager.get_service('stt') is not None
                            assert service_manager.get_service('llm') is not None
                            assert service_manager.get_service('tts') is not None
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, mock_config_validator):
        """Test graceful degradation when services fail"""
        with patch('wake_word_detector.WakeWordDetector') as mock_wake_word:
            with patch('stt_service.STTService') as mock_stt:
                with patch('storyteller_llm.StorytellerLLM') as mock_llm:
                    with patch('tts_service.TTSService') as mock_tts:
                        with patch('audio_feedback.get_audio_feedback') as mock_audio:
                            
                            # Make TTS service fail
                            mock_wake_word.return_value = Mock()
                            mock_stt.return_value = Mock()
                            mock_llm.return_value = Mock()
                            mock_tts.side_effect = Exception("TTS service failed")
                            mock_audio.return_value = Mock()
                            
                            service_manager = ServiceManager(mock_config_validator)
                            success = await service_manager.initialize_all_services()
                            
                            # Should still be able to operate with degraded TTS
                            assert service_manager.can_operate()
                            assert service_manager.get_service('tts') is None
                            
                            # Check service health
                            tts_health = service_manager.get_service_health('tts')
                            assert tts_health.status == ServiceStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_config_validator):
        """Test health check functionality"""
        with patch('wake_word_detector.WakeWordDetector') as mock_wake_word:
            with patch('stt_service.STTService') as mock_stt:
                with patch('storyteller_llm.StorytellerLLM') as mock_llm:
                    with patch('tts_service.TTSService') as mock_tts:
                        with patch('audio_feedback.get_audio_feedback') as mock_audio:
                            
                            mock_wake_word.return_value = Mock()
                            mock_stt.return_value = Mock()
                            mock_llm.return_value = Mock()
                            mock_tts.return_value = Mock()
                            mock_audio.return_value = Mock()
                            
                            service_manager = ServiceManager(mock_config_validator)
                            await service_manager.initialize_all_services()
                            
                            health_report = await service_manager.health_check()
                            
                            assert 'timestamp' in health_report
                            assert 'overall_status' in health_report
                            assert 'services' in health_report
                            assert 'system_info' in health_report
                            
                            assert health_report['overall_status'] == 'healthy'
                            assert health_report['system_info']['can_operate'] is True


class TestStorytellerApp:
    """Test main application functionality"""
    
    @pytest.fixture
    def mock_service_manager(self):
        """Create mock service manager"""
        service_manager = Mock(spec=ServiceManager)
        service_manager.can_operate.return_value = True
        service_manager.is_service_available.return_value = True
        service_manager.get_service.return_value = Mock()
        service_manager.cleanup_services = AsyncMock()
        service_manager.health_check = AsyncMock(return_value={
            'timestamp': 1234567890,
            'overall_status': 'healthy',
            'services': {},
            'system_info': {
                'can_operate': True,
                'degraded_services': [],
                'failed_services': []
            }
        })
        return service_manager
    
    @pytest.mark.asyncio
    async def test_app_initialization(self, mock_service_manager):
        """Test application initialization"""
        with patch('storyteller_main.validate_configuration') as mock_validate:
            with patch('storyteller_main.initialize_services') as mock_init_services:
                
                mock_validate.return_value = (True, Mock())
                mock_init_services.return_value = mock_service_manager
                
                app = StorytellerApp()
                
                # Initialize services
                await app._initialize_services()
                
                assert app.service_manager is not None
                assert app.service_manager.can_operate()
    
    @pytest.mark.asyncio
    async def test_wake_word_handling(self, mock_service_manager):
        """Test wake word detection and handling"""
        with patch('storyteller_main.validate_configuration') as mock_validate:
            with patch('storyteller_main.initialize_services') as mock_init_services:
                
                mock_validate.return_value = (True, Mock())
                mock_init_services.return_value = mock_service_manager
                
                # Mock services
                mock_tts = Mock()
                mock_tts.speak_text = AsyncMock()
                mock_stt = Mock()
                mock_stt.record_audio.return_value = b'fake_audio_data'
                mock_stt.transcribe_audio = AsyncMock(return_value="Tell me a story")
                mock_llm = Mock()
                mock_llm.generate_response = AsyncMock(return_value="Once upon a time...")
                
                def mock_get_service(service_name):
                    if service_name == 'tts':
                        return mock_tts
                    elif service_name == 'stt':
                        return mock_stt
                    elif service_name == 'llm':
                        return mock_llm
                    return Mock()
                
                mock_service_manager.get_service.side_effect = mock_get_service
                
                app = StorytellerApp()
                await app._initialize_services()
                
                # Test wake word handling
                await app._handle_wake_word()
                
                # Verify services were called
                mock_tts.speak_text.assert_called()
                mock_stt.record_audio.assert_called()
                mock_stt.transcribe_audio.assert_called()
                mock_llm.generate_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_service_manager):
        """Test error handling in application"""
        with patch('storyteller_main.validate_configuration') as mock_validate:
            with patch('storyteller_main.initialize_services') as mock_init_services:
                
                mock_validate.return_value = (True, Mock())
                mock_init_services.return_value = mock_service_manager
                
                # Mock services that will fail
                mock_tts = Mock()
                mock_tts.speak_text = AsyncMock(side_effect=Exception("TTS failed"))
                mock_stt = Mock()
                mock_stt.record_audio.return_value = b'fake_audio_data'
                mock_stt.transcribe_audio = AsyncMock(side_effect=Exception("STT failed"))
                
                def mock_get_service(service_name):
                    if service_name == 'tts':
                        return mock_tts
                    elif service_name == 'stt':
                        return mock_stt
                    return Mock()
                
                mock_service_manager.get_service.side_effect = mock_get_service
                
                app = StorytellerApp()
                await app._initialize_services()
                
                # Test error handling - should not crash
                try:
                    await app._handle_wake_word()
                except Exception as e:
                    pytest.fail(f"Application should handle errors gracefully: {e}")
                
                # Should have attempted to call services
                mock_tts.speak_text.assert_called()


class TestServiceInteractions:
    """Test interactions between services"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self):
        """Test complete conversation flow"""
        with patch('config_validator.load_dotenv'):
            with patch('wake_word_detector.WakeWordDetector') as mock_wake_word:
                with patch('stt_service.STTService') as mock_stt_class:
                    with patch('storyteller_llm.StorytellerLLM') as mock_llm_class:
                        with patch('tts_service.TTSService') as mock_tts_class:
                            with patch('audio_feedback.get_audio_feedback') as mock_audio:
                                
                                # Set up service mocks
                                mock_wake_word_instance = Mock()
                                mock_wake_word.return_value = mock_wake_word_instance
                                
                                mock_stt_instance = Mock()
                                mock_stt_instance.record_audio.return_value = b'test_audio'
                                mock_stt_instance.transcribe_audio = AsyncMock(return_value="Hello")
                                mock_stt_class.return_value = mock_stt_instance
                                
                                mock_llm_instance = Mock()
                                mock_llm_instance.generate_response = AsyncMock(return_value="Hello there!")
                                mock_llm_class.return_value = mock_llm_instance
                                
                                mock_tts_instance = Mock()
                                mock_tts_instance.speak_text = AsyncMock()
                                mock_tts_class.return_value = mock_tts_instance
                                
                                mock_audio.return_value = Mock()
                                
                                # Create mock validator
                                validator = Mock(spec=ConfigValidator)
                                validator.get_config.return_value = {
                                    'audio': {'sample_rate': 16000, 'channels': 1, 'chunk_size': 1024, 'input_device': 'default', 'output_device': 'default'},
                                    'wake_word': {'framework': 'openwakeword', 'model_path': '/tmp/test.onnx', 'threshold': 0.5, 'sample_rate': 16000, 'buffer_size': 1024},
                                    'stt': {'primary_service': 'google', 'language_code': 'en-US', 'timeout': 30.0, 'max_audio_length': 60.0},
                                    'llm': {'service': 'gemini', 'model': 'gemini-2.5-flash', 'temperature': 0.7, 'max_tokens': 1000, 'child_safe_mode': True},
                                    'tts': {'service': 'elevenlabs', 'voice_stability': 0.75, 'voice_similarity_boost': 0.75},
                                    'system': {'install_dir': '/opt/storytellerpi', 'log_dir': '/opt/storytellerpi/logs', 'models_dir': '/opt/storytellerpi/models', 'log_level': 'INFO', 'service_name': 'storytellerpi'}
                                }
                                
                                # Test the complete flow
                                service_manager = ServiceManager(validator)
                                await service_manager.initialize_all_services()
                                
                                # Simulate conversation
                                stt_service = service_manager.get_service('stt')
                                llm_service = service_manager.get_service('llm')
                                tts_service = service_manager.get_service('tts')
                                
                                # Record audio
                                audio_data = stt_service.record_audio(5.0)
                                assert audio_data == b'test_audio'
                                
                                # Transcribe
                                text = await stt_service.transcribe_audio(audio_data)
                                assert text == "Hello"
                                
                                # Generate response
                                response = await llm_service.generate_response(text, "conversation")
                                assert response == "Hello there!"
                                
                                # Speak response
                                await tts_service.speak_text(response)
                                mock_tts_instance.speak_text.assert_called_with("Hello there!")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])