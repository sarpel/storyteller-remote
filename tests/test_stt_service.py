"""
Tests for Speech-to-Text Service
"""

import os
import sys
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from stt_service import STTService


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
        'apis': {
            'google': {
                'credentials_path': 'credentials/test-google-creds.json',
                'language_code': 'en-US'
            },
            'openai': {
                'api_key_path': 'credentials/test-openai-key.txt',
                'model': 'whisper-1'
            }
        }
    }


@pytest.fixture
def mock_credentials(test_config):
    """Create mock credential files"""
    # Create temporary credential files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as google_creds:
        google_creds.write('{"type": "service_account", "project_id": "test"}')
        test_config['apis']['google']['credentials_path'] = google_creds.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as openai_key:
        openai_key.write('sk-test-key-123')
        test_config['apis']['openai']['api_key_path'] = openai_key.name
    
    yield test_config
    
    # Cleanup
    os.unlink(test_config['apis']['google']['credentials_path'])
    os.unlink(test_config['apis']['openai']['api_key_path'])


class TestSTTService:
    
    @patch('stt_service.GOOGLE_STT_AVAILABLE', True)
    @patch('stt_service.OPENAI_AVAILABLE', True)
    @patch('stt_service.speech.SpeechClient')
    @patch('stt_service.openai.OpenAI')
    def test_init_success(self, mock_openai, mock_speech_client, mock_credentials):
        """Test successful initialization with both services"""
        service = STTService(mock_credentials)
        
        assert service.google_client is not None
        assert service.openai_client is not None
        mock_speech_client.assert_called_once()
        mock_openai.assert_called_once()
    
    def test_init_missing_credentials(self, test_config):
        """Test initialization with missing credentials"""
        test_config['apis']['google']['credentials_path'] = 'nonexistent.json'
        test_config['apis']['openai']['api_key_path'] = 'nonexistent.txt'
        
        with patch('stt_service.GOOGLE_STT_AVAILABLE', True):
            with patch('stt_service.OPENAI_AVAILABLE', True):
                service = STTService(test_config)
                # Should handle missing files gracefully
                assert service.google_client is None
                assert service.openai_client is None
    
    @pytest.mark.asyncio
    @patch('stt_service.GOOGLE_STT_AVAILABLE', True)
    @patch('stt_service.speech.SpeechClient')
    async def test_google_transcription_success(self, mock_speech_client, mock_credentials):
        """Test successful Google Cloud transcription"""
        # Mock Google client response
        mock_client = Mock()
        mock_response = Mock()
        mock_result = Mock()
        mock_alternative = Mock()
        
        mock_alternative.transcript = "Hello world"
        mock_alternative.confidence = 0.95
        mock_result.alternatives = [mock_alternative]
        mock_response.results = [mock_result]
        mock_client.recognize.return_value = mock_response
        mock_speech_client.return_value = mock_client
        
        service = STTService(mock_credentials)
        service.google_client = mock_client
        
        # Test transcription
        audio_data = b'fake_audio_data'
        result = await service._transcribe_google(audio_data)
        
        assert result == "Hello world"
        mock_client.recognize.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stt_service.GOOGLE_STT_AVAILABLE', True)
    @patch('stt_service.speech.SpeechClient')
    async def test_google_transcription_no_results(self, mock_speech_client, mock_credentials):
        """Test Google transcription with no results"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.results = []
        mock_client.recognize.return_value = mock_response
        mock_speech_client.return_value = mock_client
        
        service = STTService(mock_credentials)
        service.google_client = mock_client
        
        audio_data = b'fake_audio_data'
        result = await service._transcribe_google(audio_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('stt_service.OPENAI_AVAILABLE', True)
    @patch('stt_service.openai.OpenAI')
    async def test_openai_transcription_success(self, mock_openai, mock_credentials):
        """Test successful OpenAI Whisper transcription"""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_transcript = Mock()
        mock_transcript.text = "Hello from Whisper"
        mock_client.audio.transcriptions.create.return_value = mock_transcript
        mock_openai.return_value = mock_client
        
        service = STTService(mock_credentials)
        service.openai_client = mock_client
        
        # Mock file operations
        with patch('builtins.open', mock_open_context_manager()):
            with patch('stt_service.tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = Mock()
                mock_temp_file.name = 'test.wav'
                mock_temp.__enter__.return_value = mock_temp_file
                
                with patch('os.unlink'):
                    with patch.object(service, '_save_audio_as_wav'):
                        audio_data = b'fake_audio_data'
                        result = await service._transcribe_openai(audio_data)
        
        assert result == "Hello from Whisper"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_fallback(self, mock_credentials):
        """Test transcription with fallback to OpenAI"""
        service = STTService(mock_credentials)
        
        # Mock Google failure, OpenAI success
        service.google_client = Mock()
        service.openai_client = Mock()
        
        with patch.object(service, '_transcribe_google', return_value=None):
            with patch.object(service, '_transcribe_openai', return_value="Fallback result"):
                audio_data = b'fake_audio_data'
                result = await service.transcribe_audio(audio_data)
        
        assert result == "Fallback result"
    
    def test_save_audio_as_wav(self, mock_credentials):
        """Test WAV file creation"""
        service = STTService(mock_credentials)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio_data = b'\x00' * 1024  # Simple audio data
            
            try:
                service._save_audio_as_wav(audio_data, temp_file.name)
                assert os.path.exists(temp_file.name)
                assert os.path.getsize(temp_file.name) > 0
            finally:
                os.unlink(temp_file.name)
    
    @patch('stt_service.pyaudio.PyAudio')
    def test_record_audio(self, mock_pyaudio, mock_credentials):
        """Test audio recording functionality"""
        service = STTService(mock_credentials)
        
        # Mock PyAudio
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.read.return_value = b'\x00' * service.chunk_size
        mock_audio.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_audio
        
        # Test recording
        duration = 1.0  # 1 second
        audio_data = service.record_audio(duration)
        
        assert len(audio_data) > 0
        mock_stream.read.assert_called()
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()


def mock_open_context_manager():
    """Helper to create a mock context manager for file operations"""
    mock_file = MagicMock()
    mock_open = MagicMock()
    mock_open.__enter__ = MagicMock(return_value=mock_file)
    mock_open.__exit__ = MagicMock(return_value=None)
    return mock_open