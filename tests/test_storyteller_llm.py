"""
Tests for Storyteller LLM Service
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from storyteller_llm import StorytellerLLM


@pytest.fixture
def test_config():
    """Create test configuration"""
    return {
        'apis': {
            'google': {
                'credentials_path': 'credentials/test-google-creds.json'
            }
        },
        'storyteller': {
            'max_conversation_length': 5,
            'story_length': 'medium',
            'safety_level': 'high',
            'system_prompt': 'You are Elsa, a friendly storyteller.'
        }
    }


class TestStorytellerLLM:
    
    @patch('storyteller_llm.GEMINI_AVAILABLE', True)
    @patch('storyteller_llm.genai.configure')
    @patch('storyteller_llm.genai.GenerativeModel')
    def test_init_success(self, mock_model, mock_configure, test_config):
        """Test successful initialization"""
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        service = StorytellerLLM(test_config)
        
        assert service.model is not None
        assert service.max_history_length == 5
        assert service.story_length == 'medium'
        assert service.safety_level == 'high'
        mock_configure.assert_called_once()
        mock_model.assert_called_once()
    
    def test_safety_settings_high(self, test_config):
        """Test high safety level settings"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
                    settings = service._get_safety_settings()
        
        # Should have strict safety settings
        assert len(settings) == 4
        assert all(setting['threshold'] in ['BLOCK_LOW_AND_ABOVE'] for setting in settings)
    
    def test_safety_settings_medium(self, test_config):
        """Test medium safety level settings"""
        test_config['storyteller']['safety_level'] = 'medium'
        
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
                    settings = service._get_safety_settings()
        
        # Should have mixed safety settings
        assert len(settings) == 4
        # At least one should be BLOCK_MEDIUM_AND_ABOVE
        medium_blocks = [s for s in settings if 'MEDIUM' in s['threshold']]
        assert len(medium_blocks) > 0
    
    def test_conversation_history_management(self, test_config):
        """Test conversation history limits"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
        
        # Add messages beyond limit
        for i in range(15):  # More than max_conversation_length * 2
            service._add_to_history("user", f"Message {i}")
            service._add_to_history("assistant", f"Response {i}")
        
        # Trigger history management
        service._manage_conversation_history()
        
        # Should be trimmed to max limit
        assert len(service.conversation_history) <= test_config['storyteller']['max_conversation_length'] * 2
    
    def test_context_determination(self, test_config):
        """Test context type determination"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
        
        # Test story requests
        story_inputs = [
            "Tell me a story",
            "I want to hear a tale",
            "Tell me about adventures"
        ]
        for input_text in story_inputs:
            prompt = service._prepare_prompt(input_text, "story_request")
            assert "story" in prompt.lower()
        
        # Test questions
        question_inputs = [
            "What is the sky blue?",
            "How do birds fly?",
            "Why do we sleep?"
        ]
        for input_text in question_inputs:
            prompt = service._prepare_prompt(input_text, "question")
            assert "question" in prompt.lower()
    
    @pytest.mark.asyncio
    @patch('storyteller_llm.GEMINI_AVAILABLE', True)
    @patch('storyteller_llm.genai.configure')
    @patch('storyteller_llm.genai.GenerativeModel')
    async def test_generate_response_success(self, mock_model, mock_configure, test_config):
        """Test successful response generation"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "Once upon a time, there was a brave princess..."
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        service = StorytellerLLM(test_config)
        
        # Mock asyncio.to_thread
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_response
            
            result = await service.generate_response("Tell me a story", "story_request")
        
        assert result == "Once upon a time, there was a brave princess..."
        assert len(service.conversation_history) == 2  # User input + assistant response
    
    @pytest.mark.asyncio
    @patch('storyteller_llm.GEMINI_AVAILABLE', True)
    @patch('storyteller_llm.genai.configure')
    @patch('storyteller_llm.genai.GenerativeModel')
    async def test_generate_response_failure(self, mock_model, mock_configure, test_config):
        """Test response generation failure"""
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance
        
        service = StorytellerLLM(test_config)
        
        with patch('asyncio.to_thread', side_effect=Exception("API Error")):
            result = await service.generate_response("Tell me a story", "story_request")
        
        assert result is None
    
    def test_prompt_preparation_with_history(self, test_config):
        """Test prompt preparation with conversation history"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
        
        # Add some conversation history
        service._add_to_history("user", "Hello")
        service._add_to_history("assistant", "Hello! I'm Elsa.")
        service._add_to_history("user", "How are you?")
        service._add_to_history("assistant", "I'm doing great!")
        
        # Test prompt includes history
        prompt = service._prepare_prompt("Tell me a story", "story_request")
        
        assert "Hello" in prompt
        assert "Elsa" in prompt
        assert "story" in prompt.lower()
    
    def test_story_length_guidance(self, test_config):
        """Test story length guidance in prompts"""
        lengths = ['short', 'medium', 'long']
        
        for length in lengths:
            test_config['storyteller']['story_length'] = length
            
            with patch('storyteller_llm.GEMINI_AVAILABLE', True):
                with patch('storyteller_llm.genai.configure'):
                    with patch('storyteller_llm.genai.GenerativeModel'):
                        service = StorytellerLLM(test_config)
            
            prompt = service._prepare_prompt("Tell me a story", "story_request")
            
            # Should contain length guidance
            if length == 'short':
                assert "100 words" in prompt
            elif length == 'medium':
                assert "100-200 words" in prompt
            elif length == 'long':
                assert "300 words" in prompt
    
    def test_clear_conversation(self, test_config):
        """Test conversation clearing"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
        
        # Add some history
        service._add_to_history("user", "Hello")
        service._add_to_history("assistant", "Hi there!")
        
        assert len(service.conversation_history) == 2
        
        service.clear_conversation()
        
        assert len(service.conversation_history) == 0
    
    def test_conversation_summary(self, test_config):
        """Test conversation summary generation"""
        with patch('storyteller_llm.GEMINI_AVAILABLE', True):
            with patch('storyteller_llm.genai.configure'):
                with patch('storyteller_llm.genai.GenerativeModel'):
                    service = StorytellerLLM(test_config)
        
        # Add some history
        service._add_to_history("user", "Hello")
        service._add_to_history("assistant", "Hi there!")
        
        summary = service.get_conversation_summary()
        
        assert summary['message_count'] == 2
        assert summary['safety_level'] == 'high'
        assert 'topics' in summary
        assert 'duration' in summary