"""
Tests for Wake Word Detector
"""

import os
import sys
import pytest
import numpy as np
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from wake_word_detector import WakeWordDetector


@pytest.fixture
def test_config():
    """Create test configuration"""
    return {
        'audio': {
            'sample_rate': 16000,
            'chunk_size': 1024,
            'channels': 1,
            'input_device': 'default'
        },
        'wake_word': {
            'model_path': 'models/test_model.onnx',
            'threshold': 0.7,
            'inference_framework': 'onnx'
        }
    }


@pytest.fixture
def mock_model_file(test_config):
    """Create a temporary model file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
        f.write(b'fake_model_data')
        test_config['wake_word']['model_path'] = f.name
        yield f.name
    os.unlink(f.name)


class TestWakeWordDetector:
    
    def test_init_missing_model_file(self, test_config):
        """Test initialization with missing model file"""
        test_config['wake_word']['model_path'] = 'nonexistent_model.onnx'
        
        with pytest.raises(FileNotFoundError):
            WakeWordDetector(test_config)
    
    @patch('wake_word_detector.OPENWAKEWORD_AVAILABLE', True)
    @patch('wake_word_detector.Model')
    @patch('wake_word_detector.pyaudio.PyAudio')
    def test_init_openwakeword_success(self, mock_pyaudio, mock_model, mock_model_file, test_config):
        """Test successful initialization with OpenWakeWord"""
        mock_audio_instance = Mock()
        mock_pyaudio.return_value = mock_audio_instance
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        
        detector = WakeWordDetector(test_config)
        
        assert detector.framework == 'onnx'
        assert detector.model is not None
        mock_model.assert_called_once()
    
    @patch('wake_word_detector.PORCUPINE_AVAILABLE', True)
    @patch('wake_word_detector.pvporcupine.create')
    @patch('wake_word_detector.pyaudio.PyAudio')
    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    def test_init_porcupine_success(self, mock_pyaudio, mock_porcupine, mock_model_file, test_config):
        """Test successful initialization with Porcupine"""
        test_config['wake_word']['inference_framework'] = 'porcupine'
        test_config['wake_word']['model_path'] = mock_model_file
        
        mock_audio_instance = Mock()
        mock_pyaudio.return_value = mock_audio_instance
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        
        detector = WakeWordDetector(test_config)
        
        assert detector.framework == 'porcupine'
        mock_porcupine.assert_called_once()
    
    @patch('wake_word_detector.OPENWAKEWORD_AVAILABLE', True)
    @patch('wake_word_detector.Model')
    @patch('wake_word_detector.pyaudio.PyAudio')
    def test_detection_callback(self, mock_pyaudio, mock_model, mock_model_file, test_config):
        """Test wake word detection callback"""
        mock_audio_instance = Mock()
        mock_pyaudio.return_value = mock_audio_instance
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        
        detector = WakeWordDetector(test_config)
        
        # Test callback setting
        callback = Mock()
        detector.set_detection_callback(callback)
        assert detector.detection_callback == callback
    
    @patch('wake_word_detector.OPENWAKEWORD_AVAILABLE', True)
    @patch('wake_word_detector.Model')
    @patch('wake_word_detector.pyaudio.PyAudio')
    def test_openwakeword_processing(self, mock_pyaudio, mock_model, mock_model_file, test_config):
        """Test OpenWakeWord audio processing"""
        mock_audio_instance = Mock()
        mock_pyaudio.return_value = mock_audio_instance
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        
        # Mock model prediction
        mock_model_instance = Mock()
        mock_model_instance.predict.return_value = {'hey_elsa': 0.8}
        mock_model.return_value = mock_model_instance
        
        detector = WakeWordDetector(test_config)
        callback = Mock()
        detector.set_detection_callback(callback)
        
        # Test audio processing
        audio_data = np.random.randint(-32768, 32767, 1024, dtype=np.int16)
        detector._process_openwakeword(audio_data)
        
        # Should trigger callback since 0.8 > 0.7 threshold
        callback.assert_called_once_with('hey_elsa', 0.8)
    
    def test_audio_device_selection(self, test_config):
        """Test audio device selection logic"""
        test_config['audio']['input_device'] = 'specific_device'
        
        with patch('wake_word_detector.pyaudio.PyAudio') as mock_pyaudio:
            mock_audio_instance = Mock()
            mock_pyaudio.return_value = mock_audio_instance
            
            # Mock device enumeration
            mock_audio_instance.get_device_count.return_value = 2
            mock_audio_instance.get_device_info_by_index.side_effect = [
                {'name': 'default_device'},
                {'name': 'specific_device_name'}
            ]
            
            mock_stream = Mock()
            mock_audio_instance.open.return_value = mock_stream
            
            with patch('wake_word_detector.OPENWAKEWORD_AVAILABLE', False):
                with patch('wake_word_detector.PORCUPINE_AVAILABLE', False):
                    with patch('wake_word_detector.TENSORFLOW_AVAILABLE', False):
                        # Should raise error due to no available framework
                        with pytest.raises(ValueError):
                            WakeWordDetector(test_config)