"""
LLM Storytelling Service for StorytellerPi
Uses Google Gemini 2.5 Flash for generating child-appropriate stories and conversations
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI not available")


class StorytellerLLM:
    """
    LLM service for generating stories and conversations for children
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.logger = logging.getLogger(__name__)
        
        # Conversation management
        self.conversation_history = []
        self.max_history_length = int(os.getenv('LLM_CONVERSATION_HISTORY_LIMIT', '10'))
        
        # Get API key from environment
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Safety and content settings from environment
        self.safety_level = os.getenv('LLM_CONTENT_FILTER_LEVEL', 'strict')
        self.story_length = os.getenv('LLM_MAX_TOKENS', '1000')
        self.child_safe_mode = os.getenv('LLM_CHILD_SAFE_MODE', 'true').lower() == 'true'
        self.age_appropriate = int(os.getenv('LLM_AGE_APPROPRIATE_CONTENT', '5'))
        
        # Create system prompt for child-appropriate content
        self.system_prompt = self._create_system_prompt()
        
        # Initialize Gemini client
        self.model = None
        self._initialize_gemini()
    
    def _create_system_prompt(self):
        """Create system prompt for child-appropriate content"""
        return f"""You are Elsa, a friendly storyteller for a {self.age_appropriate}-year-old child.

IMPORTANT GUIDELINES:
- Keep all content appropriate for age {self.age_appropriate}
- Use simple, clear language
- Be encouraging and positive
- Create engaging, imaginative stories
- Answer questions in a child-friendly way
- Avoid scary, violent, or inappropriate content
- Keep responses under {self.story_length} words
- Be patient and kind

RESPONSE TYPES:
- Stories: Create magical, fun adventures
- Questions: Answer simply and educational
- Conversations: Be friendly and engaging

Remember: You are talking to a young child. Keep everything safe, fun, and appropriate."""

    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        try:
            if not GEMINI_AVAILABLE:
                raise ImportError("Google Generative AI library not available")
            
            # Configure Gemini with API key
            genai.configure(api_key=self.api_key)
            
            # Create model with safety settings
            safety_settings = self._get_safety_settings()
            
            # Get model name from environment
            model_name = os.getenv('LLM_MODEL', 'gemini-2.5-flash')
            
            self.model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings,
                system_instruction=self.system_prompt
            )            
            self.logger.info("Google Gemini model initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def _get_safety_settings(self):
        """Configure safety settings based on safety level"""
        # Get safety settings from environment
        harassment_level = os.getenv('LLM_SAFETY_HARASSMENT', 'block_medium_and_above').upper()
        hate_speech_level = os.getenv('LLM_SAFETY_HATE_SPEECH', 'block_medium_and_above').upper()
        sexually_explicit_level = os.getenv('LLM_SAFETY_SEXUALLY_EXPLICIT', 'block_most').upper()
        dangerous_content_level = os.getenv('LLM_SAFETY_DANGEROUS_CONTENT', 'block_medium_and_above').upper()
        
        # For child safety, use strict settings regardless of config
        if self.child_safe_mode:
            return [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
            ]
        
        # Use configured levels
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": harassment_level},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": hate_speech_level},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": sexually_explicit_level},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": dangerous_content_level},
        ]
    
    async def generate_response(self, user_input: str, context_type: str = "conversation") -> Optional[str]:
        """
        Generate a response based on user input
        
        Args:
            user_input: The child's spoken input
            context_type: Type of interaction ("conversation", "story_request", "question")
            
        Returns:
            Generated response text or None if failed
        """
        try:
            # Prepare prompt based on context
            prompt = self._prepare_prompt(user_input, context_type)
            
            # Add to conversation history
            self._add_to_history("user", user_input)
            
            # Generate response
            response = await self._generate_with_gemini(prompt)
            
            if response:
                # Add response to history
                self._add_to_history("assistant", response)
                
                # Clean up history if too long
                self._manage_conversation_history()
                
                self.logger.info(f"Generated response for '{user_input[:50]}...'")
                return response
            else:
                self.logger.error("Failed to generate response")
                return None
                
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return None    
    def _prepare_prompt(self, user_input: str, context_type: str) -> str:
        """Prepare prompt based on context and conversation history"""
        
        # Base context based on type
        if context_type == "story_request":
            context = "The child is asking for a story. Create an engaging, age-appropriate story."
        elif context_type == "question":
            context = "The child has asked a question. Provide a helpful, educational answer."
        else:
            context = "Continue the conversation naturally."
        
        # Story length guidance
        length_guide = {
            "short": "Keep the story under 100 words.",
            "medium": "Keep the story between 100-200 words.",
            "long": "The story can be up to 300 words."
        }
        
        if context_type == "story_request":
            context += f" {length_guide.get(self.story_length, length_guide['medium'])}"
        
        # Build prompt with conversation history
        prompt_parts = [
            f"Context: {context}",
            "",
            "Recent conversation:"
        ]
        
        # Add recent conversation history
        for entry in self.conversation_history[-6:]:  # Last 3 exchanges
            role = "Child" if entry["role"] == "user" else "Elsa"
            prompt_parts.append(f"{role}: {entry['content']}")
        
        # Add current input
        prompt_parts.extend([
            f"Child: {user_input}",
            "",
            "Elsa:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        """Generate response using Gemini"""
        try:
            # Generate content
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 300,
                }
            )
            
            if response.text:
                return response.text.strip()
            else:
                self.logger.warning("Gemini returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {e}")
            return None
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def _manage_conversation_history(self):
        """Keep conversation history within limits"""
        if len(self.conversation_history) > self.max_history_length * 2:  # *2 for user+assistant pairs
            # Remove oldest entries, keeping pairs
            self.conversation_history = self.conversation_history[-(self.max_history_length * 2):]
            self.logger.debug("Conversation history trimmed")
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        return {
            "message_count": len(self.conversation_history),
            "duration": None,  # Could calculate from timestamps
            "topics": [],  # Could analyze conversation topics
            "safety_level": self.safety_level
        }