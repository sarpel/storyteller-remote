"""
Tests for Text-to-Speech Service
"""

import os
import sys
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock, mock_open
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from tts_service import TTSService


@pytest.fixture
def test_config():
    """Create test configuration"""
    return {
        'audio': {
            'output_device': 'default'
        },
        'apis': {
            'elevenlabs': {
                'api_key_path': 'credentials/test-elevenlabs-key.txt',
                'voice_id': 'test_voice_id',
                'model_id': 'eleven_multilingual_v2',
                'stability': 0.5,
                'similarity_boost': 0.8
            }
        },
        'storyteller': {
            'voice_speed': 0.8
        }
    }


@pytest.fixture
def mock_credentials(test_config):
    """Create mock credential files"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as api_key:
        api_key.write('test_elevenlabs_api_key')
        test_config['apis']['elevenlabs']['api_key_path'] = api_key.name
    
    yield test_config
    
    # Cleanup
    os.unlink(test_config['apis']['elevenlabs']['api_key_path'])


class TestTTSService:
    
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    def test_init_success(self, mock_mixer_init, mock_mixer_pre_init, mock_set_api_key, mock_credentials):
        """Test successful initialization"""
        service = TTSService(mock_credentials)
        
        assert service.voice_id == 'test_voice_id'
        assert service.model_id == 'eleven_multilingual_v2'
        assert service.stability == 0.5
        assert service.similarity_boost == 0.8
        assert service.voice_speed == 0.8
        
        mock_set_api_key.assert_called_once_with('test_elevenlabs_api_key')
        mock_mixer_pre_init.assert_called_once()
        mock_mixer_init.assert_called_once()
    
    def test_init_missing_api_key(self, test_config):
        """Test initialization with missing API key"""
        test_config['apis']['elevenlabs']['api_key_path'] = 'nonexistent.txt'
        
        with patch('tts_service.ELEVENLABS_AVAILABLE', True):
            with pytest.raises(FileNotFoundError):
                TTSService(test_config)
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    @patch('tts_service.generate')
    async def test_generate_audio_success(self, mock_generate, mock_mixer_init, 
                                        mock_mixer_pre_init, mock_set_api_key, mock_credentials):
        """Test successful audio generation"""
        # Mock ElevenLabs response
        mock_audio_data = b'fake_audio_data'
        
        # Create mock for asyncio.to_thread
        async def mock_to_thread(func, *args, **kwargs):
            return mock_audio_data
        
        service = TTSService(mock_credentials)
        
        with patch('asyncio.to_thread', side_effect=mock_to_thread):
            result = await service._generate_audio("Hello world")
        
        assert result == mock_audio_data
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    @patch('tts_service.generate')
    async def test_generate_audio_generator_response(self, mock_generate, mock_mixer_init,
                                                   mock_mixer_pre_init, mock_set_api_key, mock_credentials):
        """Test audio generation with generator response"""
        # Mock generator response
        def mock_audio_generator():
            yield b'chunk1'
            yield b'chunk2'
            yield b'chunk3'
        
        async def mock_to_thread(func, *args, **kwargs):
            return mock_audio_generator()
        
        service = TTSService(mock_credentials)
        
        with patch('asyncio.to_thread', side_effect=mock_to_thread):
            result = await service._generate_audio("Hello world")
        
        assert result == b'chunk1chunk2chunk3'
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    async def test_play_audio_success(self, mock_mixer_init, mock_mixer_pre_init, 
                                    mock_set_api_key, mock_credentials):
        """Test successful audio playback"""
        service = TTSService(mock_credentials)
        
        with patch('tts_service.pygame.mixer.music.load') as mock_load:
            with patch('tts_service.pygame.mixer.music.play') as mock_play:
                with patch('tts_service.pygame.mixer.music.get_busy', side_effect=[True, True, False]) as mock_busy:
                    with patch('asyncio.sleep') as mock_sleep:
                        result = await service._play_audio('test.mp3')
        
        assert result is True
        mock_load.assert_called_once_with('test.mp3')
        mock_play.assert_called_once()
        assert mock_sleep.call_count == 2  # Should sleep twice while busy
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    async def test_speak_text_full_pipeline(self, mock_mixer_init, mock_mixer_pre_init,
                                          mock_set_api_key, mock_credentials):
        """Test complete speak text pipeline"""
        service = TTSService(mock_credentials)
        
        # Mock audio generation
        mock_audio_data = b'fake_audio_data'
        
        with patch.object(service, '_generate_audio', return_value=mock_audio_data) as mock_gen:
            with patch.object(service, '_play_audio', return_value=True) as mock_play:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    with patch('os.unlink') as mock_unlink:
                        # Mock temporary file
                        mock_temp_file = Mock()
                        mock_temp_file.name = 'temp_audio.mp3'
                        mock_temp_file.write = Mock()
                        mock_temp.__enter__.return_value = mock_temp_file
                        
                        result = await service.speak_text("Hello world")
        
        assert result is True
        mock_gen.assert_called_once_with("Hello world")
        mock_play.assert_called_once()
        mock_temp_file.write.assert_called_once_with(mock_audio_data)
        mock_unlink.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    async def test_speak_text_with_save(self, mock_mixer_init, mock_mixer_pre_init,
                                      mock_set_api_key, mock_credentials):
        """Test speak text with audio saving"""
        service = TTSService(mock_credentials)
        
        mock_audio_data = b'fake_audio_data'
        
        with patch.object(service, '_generate_audio', return_value=mock_audio_data):
            with patch.object(service, '_play_audio', return_value=True):
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    with patch('builtins.open', mock_open()) as mock_file:
                        with patch('os.unlink'):
                            with patch('asyncio.get_event_loop') as mock_loop:
                                mock_loop.return_value.time.return_value = 1234567890
                                
                                mock_temp_file = Mock()
                                mock_temp_file.name = 'temp_audio.mp3'
                                mock_temp_file.write = Mock()
                                mock_temp.__enter__.return_value = mock_temp_file
                                
                                result = await service.speak_text("Hello world", save_audio=True)
        
        assert result is True
        # Should have written to save file
        mock_file.assert_called()
    
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    def test_stop_playback(self, mock_mixer_init, mock_mixer_pre_init,
                          mock_set_api_key, mock_credentials):
        """Test stopping audio playback"""
        service = TTSService(mock_credentials)
        
        with patch('tts_service.pygame.mixer.music.stop') as mock_stop:
            service.stop_playback()
        
        mock_stop.assert_called_once()
    
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    def test_is_playing(self, mock_mixer_init, mock_mixer_pre_init,
                       mock_set_api_key, mock_credentials):
        """Test checking if audio is playing"""
        service = TTSService(mock_credentials)
        
        with patch('tts_service.pygame.mixer.music.get_busy', return_value=True) as mock_busy:
            result = service.is_playing()
        
        assert result is True
        mock_busy.assert_called_once()
    
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    def test_cleanup(self, mock_mixer_init, mock_mixer_pre_init,
                    mock_set_api_key, mock_credentials):
        """Test resource cleanup"""
        service = TTSService(mock_credentials)
        
        with patch('tts_service.pygame.mixer.music.stop') as mock_stop:
            with patch('tts_service.pygame.mixer.quit') as mock_quit:
                service.cleanup()
        
        mock_stop.assert_called_once()
        mock_quit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('tts_service.ELEVENLABS_AVAILABLE', True)
    @patch('tts_service.set_api_key')
    @patch('tts_service.pygame.mixer.pre_init')
    @patch('tts_service.pygame.mixer.init')
    async def test_test_voice(self, mock_mixer_init, mock_mixer_pre_init,
                            mock_set_api_key, mock_credentials):
        """Test voice testing functionality"""
        service = TTSService(mock_credentials)
        
        with patch.object(service, 'speak_text', return_value=True) as mock_speak:
            result = await service.test_voice()
        
        assert result is True
        mock_speak.assert_called_once()
        # Check that it was called with save_audio=True
        args, kwargs = mock_speak.call_args
        assert kwargs.get('save_audio') is True