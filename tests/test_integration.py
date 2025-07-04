"""
Integration tests for StorytellerPi
Tests the complete flow and component interactions
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

from storyteller_main import StorytellerApp, AppState


@pytest.fixture
def test_config_file():
    """Create a temporary configuration file"""
    config_content = """
audio:
  input_device: "default"
  output_device: "default"
  sample_rate: 16000
  chunk_size: 1024
  channels: 1

wake_word:
  model_path: "models/test_model.onnx"
  threshold: 0.7
  inference_framework: "onnx"

apis:
  google:
    credentials_path: "credentials/test-google-creds.json"
    project_id: "test-project"
    language_code: "en-US"
  openai:
    api_key_path: "credentials/test-openai-key.txt"
    model: "whisper-1"
  elevenlabs:
    api_key_path: "credentials/test-elevenlabs-key.txt"
    voice_id: "test_voice_id"
    model_id: "eleven_multilingual_v2"
    stability: 0.5
    similarity_boost: 0.8

storyteller:
  max_conversation_length: 5
  story_length: "medium"
  voice_speed: 0.8
  safety_level: "high"
  system_prompt: "You are Elsa, a friendly storyteller."

performance:
  max_memory_mb: 400
  audio_buffer_size: 4096
  processing_timeout: 10

logging:
  level: "INFO"
  file_path: "logs/test_storyteller.log"

system:
  auto_start: false
  graceful_shutdown: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        yield f.name
    
    os.unlink(f.name)


@pytest.fixture
def mock_credentials():
    """Create mock credential files"""
    credentials = {}
    
    # Google credentials
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"type": "service_account", "project_id": "test"}')
        credentials['google'] = f.name
    
    # OpenAI key
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('sk-test-key-123')
        credentials['openai'] = f.name
    
    # ElevenLabs key
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('test_elevenlabs_key')
        credentials['elevenlabs'] = f.name
    
    yield credentials
    
    # Cleanup
    for file_path in credentials.values():
        os.unlink(file_path)


class TestStorytellerIntegration:
    
    @patch('storyteller_main.os.makedirs')
    @patch('storyteller_main.logging.basicConfig')
    def test_app_initialization(self, mock_logging, mock_makedirs, test_config_file):
        """Test complete application initialization"""
        with patch('storyteller_main.WakeWordDetector') as mock_wake:
            with patch('storyteller_main.STTService') as mock_stt:
                with patch('storyteller_main.StorytellerLLM') as mock_llm:
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        assert app.config is not None
        assert app.state == AppState.IDLE
        assert app.wake_word_detector is not None
        assert app.stt_service is not None
        assert app.llm_service is not None
        assert app.tts_service is not None
    
    def test_state_transitions(self, test_config_file):
        """Test application state transitions"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService'):
                with patch('storyteller_main.StorytellerLLM'):
                    with patch('storyteller_main.TTSService'):
                        app = StorytellerApp(test_config_file)
        
        # Test state changes
        assert app.state == AppState.IDLE
        
        app._set_state(AppState.LISTENING)
        assert app.state == AppState.LISTENING
        
        app._set_state(AppState.PROCESSING)
        assert app.state == AppState.PROCESSING
        
        app._set_state(AppState.SPEAKING)
        assert app.state == AppState.SPEAKING
        
        app._set_state(AppState.IDLE)
        assert app.state == AppState.IDLE
    
    @pytest.mark.asyncio
    async def test_wake_word_detection_flow(self, test_config_file):
        """Test wake word detection triggers conversation flow"""
        with patch('storyteller_main.WakeWordDetector') as mock_wake:
            with patch('storyteller_main.STTService') as mock_stt:
                with patch('storyteller_main.StorytellerLLM') as mock_llm:
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        # Mock the complete flow
        mock_tts_instance = Mock()
        mock_tts_instance.speak_text = AsyncMock(return_value=True)
        mock_tts.return_value = mock_tts_instance
        app.tts_service = mock_tts_instance
        
        mock_stt_instance = Mock()
        mock_stt_instance.record_audio.return_value = b'fake_audio'
        mock_stt.return_value = mock_stt_instance
        app.stt_service = mock_stt_instance
        
        # Test wake word callback
        with patch.object(app, '_process_user_input', new_callable=AsyncMock) as mock_process:
            await app._handle_wake_word()
        
        # Should have played greeting and recorded audio
        mock_tts_instance.speak_text.assert_called()
        mock_stt_instance.record_audio.assert_called_once()
        mock_process.assert_called_once_with(b'fake_audio')
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, test_config_file):
        """Test complete conversation flow from STT to TTS"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService') as mock_stt:
                with patch('storyteller_main.StorytellerLLM') as mock_llm:
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        # Mock services
        mock_stt_instance = Mock()
        mock_stt_instance.transcribe_audio = AsyncMock(return_value="Tell me a story")
        app.stt_service = mock_stt_instance
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_response = AsyncMock(return_value="Once upon a time...")
        app.llm_service = mock_llm_instance
        
        mock_tts_instance = Mock()
        mock_tts_instance.speak_text = AsyncMock(return_value=True)
        app.tts_service = mock_tts_instance
        
        # Test complete flow
        audio_data = b'fake_audio_data'
        await app._process_user_input(audio_data)
        
        # Verify all steps were called
        mock_stt_instance.transcribe_audio.assert_called_once_with(audio_data)
        mock_llm_instance.generate_response.assert_called_once_with("Tell me a story", "story_request")
        mock_tts_instance.speak_text.assert_called()
    
    def test_context_type_determination(self, test_config_file):
        """Test context type determination for different inputs"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService'):
                with patch('storyteller_main.StorytellerLLM'):
                    with patch('storyteller_main.TTSService'):
                        app = StorytellerApp(test_config_file)
        
        # Test story requests
        assert app._determine_context_type("Tell me a story") == "story_request"
        assert app._determine_context_type("I want to hear a tale") == "story_request"
        
        # Test questions
        assert app._determine_context_type("What is the sky blue?") == "question"
        assert app._determine_context_type("How do birds fly?") == "question"
        assert app._determine_context_type("Why do we sleep?") == "question"
        
        # Test general conversation
        assert app._determine_context_type("Hello") == "conversation"
        assert app._determine_context_type("I'm happy today") == "conversation"
    
    @pytest.mark.asyncio
    async def test_long_response_chunking(self, test_config_file):
        """Test long response text chunking"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService'):
                with patch('storyteller_main.StorytellerLLM'):
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        mock_tts_instance = Mock()
        mock_tts_instance.speak_text = AsyncMock(return_value=True)
        app.tts_service = mock_tts_instance
        
        # Create a long response that should be chunked
        long_response = "This is a very long story. " * 20  # > 200 characters
        
        await app._speak_response(long_response)
        
        # Should have been called multiple times for chunks
        assert mock_tts_instance.speak_text.call_count > 1
    
    @pytest.mark.asyncio
    async def test_error_handling_stt_failure(self, test_config_file):
        """Test error handling when STT fails"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService') as mock_stt:
                with patch('storyteller_main.StorytellerLLM'):
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        # Mock STT failure
        mock_stt_instance = Mock()
        mock_stt_instance.transcribe_audio = AsyncMock(return_value=None)
        app.stt_service = mock_stt_instance
        
        mock_tts_instance = Mock()
        mock_tts_instance.speak_text = AsyncMock(return_value=True)
        app.tts_service = mock_tts_instance
        
        audio_data = b'fake_audio_data'
        await app._process_user_input(audio_data)
        
        # Should have spoken error message
        mock_tts_instance.speak_text.assert_called()
        error_message = mock_tts_instance.speak_text.call_args[0][0]
        assert "couldn't understand" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_llm_failure(self, test_config_file):
        """Test error handling when LLM fails"""
        with patch('storyteller_main.WakeWordDetector'):
            with patch('storyteller_main.STTService') as mock_stt:
                with patch('storyteller_main.StorytellerLLM') as mock_llm:
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        # Mock successful STT but failed LLM
        mock_stt_instance = Mock()
        mock_stt_instance.transcribe_audio = AsyncMock(return_value="Tell me a story")
        app.stt_service = mock_stt_instance
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_response = AsyncMock(return_value=None)
        app.llm_service = mock_llm_instance
        
        mock_tts_instance = Mock()
        mock_tts_instance.speak_text = AsyncMock(return_value=True)
        app.tts_service = mock_tts_instance
        
        audio_data = b'fake_audio_data'
        await app._process_user_input(audio_data)
        
        # Should have spoken error message
        mock_tts_instance.speak_text.assert_called()
        error_message = mock_tts_instance.speak_text.call_args[0][0]
        assert "trouble thinking" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_cleanup_resources(self, test_config_file):
        """Test proper resource cleanup"""
        with patch('storyteller_main.WakeWordDetector') as mock_wake:
            with patch('storyteller_main.STTService'):
                with patch('storyteller_main.StorytellerLLM'):
                    with patch('storyteller_main.TTSService') as mock_tts:
                        app = StorytellerApp(test_config_file)
        
        # Mock cleanup methods
        mock_wake_instance = Mock()
        mock_wake_instance.cleanup = Mock()
        app.wake_word_detector = mock_wake_instance
        
        mock_tts_instance = Mock()
        mock_tts_instance.cleanup = Mock()
        app.tts_service = mock_tts_instance
        
        await app._cleanup()
        
        mock_wake_instance.cleanup.assert_called_once()
        mock_tts_instance.cleanup.assert_called_once()