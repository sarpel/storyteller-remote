#!/usr/bin/env python3
"""
Mock services for testing StorytellerPi
Provides lightweight implementations for testing without external dependencies
"""

import asyncio
import logging
import random
from typing import Optional, List, Dict, Any
from unittest.mock import Mock, AsyncMock

logger = logging.getLogger(__name__)


class MockWakeWordDetector:
    """Mock wake word detector for testing"""
    
    def __init__(self):
        self.is_running = False
        self.detection_callback = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def set_detection_callback(self, callback):
        """Set callback for wake word detection"""
        self.detection_callback = callback
    
    def start_detection(self):
        """Start mock detection"""
        self.is_running = True
        self.logger.info("Mock wake word detection started")
    
    def stop_detection(self):
        """Stop mock detection"""
        self.is_running = False
        self.logger.info("Mock wake word detection stopped")
    
    def simulate_wake_word(self, wake_word: str = "hey_elsa", confidence: float = 0.8):
        """Simulate wake word detection"""
        if self.detection_callback and self.is_running:
            self.detection_callback(wake_word, confidence)
    
    def cleanup(self):
        """Clean up mock detector"""
        self.stop_detection()


class MockSTTService:
    """Mock speech-to-text service for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        
        # Pre-defined responses for testing
        self.test_responses = [
            "Tell me a story",
            "What is the weather like?", 
            "How are you today?",
            "Sing me a song",
            "Tell me about dinosaurs"
        ]
    
    def record_audio(self, duration: float = 5.0) -> bytes:
        """Mock audio recording"""
        self.logger.info(f"Mock recording audio for {duration} seconds")
        # Return fake audio data
        return b'mock_audio_data_' + str(int(duration * 1000)).encode()
    
    async def transcribe_audio(self, audio_data: bytes, use_fallback: bool = True) -> Optional[str]:
        """Mock audio transcription"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if not audio_data:
            return None
        
        # Return random test response
        response = random.choice(self.test_responses)
        self.logger.info(f"Mock STT result: '{response}'")
        return response
    
    def cleanup(self):
        """Clean up mock STT service"""
        pass


class MockStorytellerLLM:
    """Mock LLM service for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.conversation_history = []
        self.max_history_length = 10
        
        # Pre-defined story responses
        self.story_responses = [
            "Once upon a time, there was a brave little mouse who lived in a big castle...",
            "In a magical forest far, far away, there lived a friendly dragon who loved to paint...",
            "There was once a young girl who could talk to animals, and one day...",
            "Long ago, in a kingdom made of clouds, there lived a kind prince who...",
            "In the deepest part of the ocean, there was a mermaid who discovered..."
        ]
        
        # Pre-defined question responses
        self.question_responses = [
            "That's a great question! Let me explain it in a simple way...",
            "I'm happy to help you learn about that!",
            "What an interesting thing to ask about!",
            "That's something very special, let me tell you why...",
            "I love when curious minds ask such wonderful questions!"
        ]
        
        # Pre-defined conversation responses
        self.conversation_responses = [
            "I'm doing wonderfully, thank you for asking!",
            "That sounds really interesting! Tell me more!",
            "I'm here and ready to chat with you!",
            "What a lovely thing to say!",
            "I enjoy talking with you so much!"
        ]
    
    async def generate_response(self, user_input: str, context_type: str = "conversation") -> Optional[str]:
        """Mock response generation"""
        await asyncio.sleep(0.2)  # Simulate processing time
        
        if not user_input:
            return None
        
        # Add to conversation history
        self._add_to_history("user", user_input)
        
        # Generate appropriate response based on context
        if context_type == "story_request":
            response = random.choice(self.story_responses)
        elif context_type == "question":
            response = random.choice(self.question_responses)
        else:
            response = random.choice(self.conversation_responses)
        
        # Add response to history
        self._add_to_history("assistant", response)
        
        self.logger.info(f"Mock LLM response for '{user_input[:30]}...': '{response[:50]}...'")
        return response
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Manage history length
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-(self.max_history_length * 2):]
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary"""
        return {
            "message_count": len(self.conversation_history),
            "safety_level": "strict",
            "topics": ["general"],
            "duration": None
        }


class MockTTSService:
    """Mock text-to-speech service for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.voice_id = "mock_voice"
        self.is_playing = False
        self.spoken_texts = []  # Track what was spoken for testing
    
    async def speak_text(self, text: str, save_audio: bool = False) -> bool:
        """Mock text-to-speech"""
        if not text:
            return False
        
        self.is_playing = True
        
        # Simulate speaking time (1 second per 10 characters)
        speaking_time = max(0.5, len(text) / 10.0)
        
        self.logger.info(f"Mock TTS speaking: '{text[:50]}...' (duration: {speaking_time:.1f}s)")
        self.spoken_texts.append(text)
        
        await asyncio.sleep(speaking_time)
        
        self.is_playing = False
        return True
    
    def stop_playback(self):
        """Stop mock playback"""
        self.is_playing = False
        self.logger.info("Mock TTS playback stopped")
    
    def is_playing(self) -> bool:
        """Check if mock TTS is playing"""
        return self.is_playing
    
    def get_spoken_texts(self) -> List[str]:
        """Get list of spoken texts (for testing)"""
        return self.spoken_texts.copy()
    
    def clear_spoken_texts(self):
        """Clear spoken texts history"""
        self.spoken_texts = []
    
    def cleanup(self):
        """Clean up mock TTS service"""
        self.stop_playback()
    
    async def test_voice(self, test_text: str = "Hello! This is a test.") -> bool:
        """Test mock voice"""
        return await self.speak_text(test_text, save_audio=True)


class MockAudioFeedback:
    """Mock audio feedback for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = True
        self.volume = 0.3
        self.feedback_history = []  # Track feedback for testing
    
    def wake_word_detected(self):
        """Mock wake word feedback"""
        self.logger.debug("Mock wake word feedback played")
        self.feedback_history.append("wake_word")
    
    def button_pressed(self):
        """Mock button press feedback"""
        self.logger.debug("Mock button press feedback played")
        self.feedback_history.append("button_press")
    
    def success_feedback(self):
        """Mock success feedback"""
        self.logger.debug("Mock success feedback played")
        self.feedback_history.append("success")
    
    def error_feedback(self):
        """Mock error feedback"""
        self.logger.debug("Mock error feedback played")
        self.feedback_history.append("error")
    
    def listening_started(self):
        """Mock listening started feedback"""
        self.wake_word_detected()
    
    def listening_stopped(self):
        """Mock listening stopped feedback"""
        self.logger.debug("Mock listening stopped feedback played")
        self.feedback_history.append("listening_stopped")
    
    def set_volume(self, volume: float):
        """Set mock feedback volume"""
        self.volume = max(0.0, min(1.0, volume))
        self.logger.info(f"Mock audio feedback volume set to {self.volume}")
    
    def set_enabled(self, enabled: bool):
        """Enable/disable mock feedback"""
        self.enabled = enabled
        self.logger.info(f"Mock audio feedback {'enabled' if enabled else 'disabled'}")
    
    def get_feedback_history(self) -> List[str]:
        """Get feedback history (for testing)"""
        return self.feedback_history.copy()
    
    def clear_feedback_history(self):
        """Clear feedback history"""
        self.feedback_history = []
    
    def test_feedback(self):
        """Test all feedback sounds"""
        self.logger.info("Testing mock audio feedback sounds...")
        self.wake_word_detected()
        self.button_pressed()
        self.success_feedback()
        self.error_feedback()
        self.logger.info("Mock audio feedback test completed")
    
    def cleanup(self):
        """Clean up mock audio feedback"""
        self.logger.info("Mock audio feedback cleaned up")


class MockWebInterface:
    """Mock web interface for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_running = False
        self.port = 8080
        self.host = "0.0.0.0"
    
    async def start(self):
        """Start mock web interface"""
        self.is_running = True
        self.logger.info(f"Mock web interface started on {self.host}:{self.port}")
    
    async def stop(self):
        """Stop mock web interface"""
        self.is_running = False
        self.logger.info("Mock web interface stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get mock web interface status"""
        return {
            "running": self.is_running,
            "host": self.host,
            "port": self.port,
            "connections": 0
        }


# Factory functions for creating mock services
def create_mock_wake_word_detector():
    """Create mock wake word detector"""
    return MockWakeWordDetector()


def create_mock_stt_service():
    """Create mock STT service"""
    return MockSTTService()


def create_mock_llm_service():
    """Create mock LLM service"""
    return MockStorytellerLLM()


def create_mock_tts_service():
    """Create mock TTS service"""
    return MockTTSService()


def create_mock_audio_feedback():
    """Create mock audio feedback"""
    return MockAudioFeedback()


def create_mock_web_interface():
    """Create mock web interface"""
    return MockWebInterface()


# Mock service factory
class MockServiceFactory:
    """Factory for creating mock services"""
    
    @staticmethod
    def create_all_services() -> Dict[str, Any]:
        """Create all mock services"""
        return {
            'wake_word': create_mock_wake_word_detector(),
            'stt': create_mock_stt_service(),
            'llm': create_mock_llm_service(),
            'tts': create_mock_tts_service(),
            'audio_feedback': create_mock_audio_feedback(),
            'web_interface': create_mock_web_interface()
        }
    
    @staticmethod
    def create_service(service_type: str) -> Any:
        """Create specific mock service"""
        factory_map = {
            'wake_word': create_mock_wake_word_detector,
            'stt': create_mock_stt_service,
            'llm': create_mock_llm_service,
            'tts': create_mock_tts_service,
            'audio_feedback': create_mock_audio_feedback,
            'web_interface': create_mock_web_interface
        }
        
        if service_type in factory_map:
            return factory_map[service_type]()
        else:
            raise ValueError(f"Unknown service type: {service_type}")


if __name__ == "__main__":
    # Test mock services
    import asyncio
    
    async def test_mock_services():
        logging.basicConfig(level=logging.INFO)
        
        print("Testing Mock Services")
        print("=" * 50)
        
        # Test all services
        services = MockServiceFactory.create_all_services()
        
        # Test wake word detection
        wake_word = services['wake_word']
        wake_word.start_detection()
        wake_word.simulate_wake_word()
        
        # Test STT
        stt = services['stt']
        audio_data = stt.record_audio(3.0)
        text = await stt.transcribe_audio(audio_data)
        print(f"STT Result: {text}")
        
        # Test LLM
        llm = services['llm']
        response = await llm.generate_response(text, "story_request")
        print(f"LLM Response: {response[:50]}...")
        
        # Test TTS
        tts = services['tts']
        await tts.speak_text(response)
        print(f"TTS Spoken: {len(tts.get_spoken_texts())} texts")
        
        # Test audio feedback
        audio_feedback = services['audio_feedback']
        audio_feedback.test_feedback()
        print(f"Audio Feedback History: {audio_feedback.get_feedback_history()}")
        
        # Cleanup
        for service in services.values():
            if hasattr(service, 'cleanup'):
                service.cleanup()
        
        print("\nMock services test completed!")
    
    asyncio.run(test_mock_services())