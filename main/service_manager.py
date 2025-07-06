#!/usr/bin/env python3
"""
Service Manager for StorytellerPi
Handles service initialization with graceful degradation
"""

import os
import time
import logging
import asyncio
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
from config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class ServiceHealth:
    """Service health information"""
    status: ServiceStatus
    message: str
    last_check: float
    error: Optional[str] = None
    fallback_available: bool = False


class ServiceManager:
    """Manages all StorytellerPi services with graceful degradation"""
    
    def __init__(self, config_validator: ConfigValidator):
        self.config = config_validator.get_config()
        self.validator = config_validator
        self.logger = logging.getLogger(__name__)
        
        # Service health tracking
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # Service instances
        self.services = {
            'wake_word': None,
            'stt': None,
            'llm': None,
            'tts': None,
            'audio_feedback': None,
            'web_interface': None
        }
        
        # Fallback services
        self.fallback_services = {
            'stt': None,  # OpenAI Whisper fallback
            'tts': None,  # System TTS fallback
            'wake_word': None  # Button fallback
        }
        
        # Service dependencies
        self.dependencies = {
            'wake_word': [],
            'stt': [],
            'llm': [],
            'tts': [],
            'audio_feedback': [],
            'web_interface': ['wake_word', 'stt', 'llm', 'tts']
        }
    
    async def initialize_all_services(self) -> bool:
        """Initialize all services with error handling"""
        self.logger.info("Initializing StorytellerPi services...")
        
        # Initialize services in dependency order
        service_order = ['audio_feedback', 'wake_word', 'stt', 'llm', 'tts', 'web_interface']
        
        overall_success = True
        
        for service_name in service_order:
            try:
                success = await self._initialize_service(service_name)
                if not success:
                    overall_success = False
                    # Try to initialize fallback if available
                    if service_name in self.fallback_services:
                        fallback_success = await self._initialize_fallback_service(service_name)
                        if fallback_success:
                            self.logger.info(f"Fallback service initialized for {service_name}")
                        else:
                            self.logger.error(f"Both primary and fallback services failed for {service_name}")
                    
            except Exception as e:
                self.logger.error(f"Critical error initializing {service_name}: {e}")
                overall_success = False
        
        # Report overall status
        self._report_service_status()
        
        return overall_success
    
    async def _initialize_service(self, service_name: str) -> bool:
        """Initialize a specific service"""
        try:
            self.logger.info(f"Initializing {service_name} service...")
            
            if service_name == 'wake_word':
                return await self._initialize_wake_word_service()
            elif service_name == 'stt':
                return await self._initialize_stt_service()
            elif service_name == 'llm':
                return await self._initialize_llm_service()
            elif service_name == 'tts':
                return await self._initialize_tts_service()
            elif service_name == 'audio_feedback':
                return await self._initialize_audio_feedback_service()
            elif service_name == 'web_interface':
                return await self._initialize_web_interface_service()
            else:
                self.logger.error(f"Unknown service: {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize {service_name}: {e}")
            self._update_service_health(service_name, ServiceStatus.FAILED, str(e))
            return False
    
    async def _initialize_wake_word_service(self) -> bool:
        """Initialize wake word detection service"""
        try:
            from wake_word_detector import WakeWordDetector
            
            self.services['wake_word'] = WakeWordDetector()
            self._update_service_health('wake_word', ServiceStatus.AVAILABLE, "Wake word service initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"Wake word detection libraries not available: {e}")
            self._update_service_health('wake_word', ServiceStatus.UNAVAILABLE, 
                                      "Wake word libraries not available", str(e), True)
            return False
        except Exception as e:
            self.logger.error(f"Wake word service initialization failed: {e}")
            self._update_service_health('wake_word', ServiceStatus.FAILED, 
                                      "Wake word service failed", str(e))
            return False
    
    async def _initialize_stt_service(self) -> bool:
        """Initialize speech-to-text service"""
        try:
            from stt_service import STTService
            
            self.services['stt'] = STTService()
            self._update_service_health('stt', ServiceStatus.AVAILABLE, "STT service initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"STT libraries not available: {e}")
            self._update_service_health('stt', ServiceStatus.UNAVAILABLE, 
                                      "STT libraries not available", str(e), True)
            return False
        except Exception as e:
            self.logger.error(f"STT service initialization failed: {e}")
            self._update_service_health('stt', ServiceStatus.FAILED, 
                                      "STT service failed", str(e))
            return False
    
    async def _initialize_llm_service(self) -> bool:
        """Initialize LLM service"""
        try:
            from storyteller_llm import StorytellerLLM
            
            self.services['llm'] = StorytellerLLM()
            self._update_service_health('llm', ServiceStatus.AVAILABLE, "LLM service initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"LLM libraries not available: {e}")
            self._update_service_health('llm', ServiceStatus.UNAVAILABLE, 
                                      "LLM libraries not available", str(e))
            return False
        except Exception as e:
            self.logger.error(f"LLM service initialization failed: {e}")
            self._update_service_health('llm', ServiceStatus.FAILED, 
                                      "LLM service failed", str(e))
            return False
    
    async def _initialize_tts_service(self) -> bool:
        """Initialize text-to-speech service"""
        try:
            from tts_service import TTSService
            
            self.services['tts'] = TTSService()
            self._update_service_health('tts', ServiceStatus.AVAILABLE, "TTS service initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"TTS libraries not available: {e}")
            self._update_service_health('tts', ServiceStatus.UNAVAILABLE, 
                                      "TTS libraries not available", str(e), True)
            return False
        except Exception as e:
            self.logger.error(f"TTS service initialization failed: {e}")
            self._update_service_health('tts', ServiceStatus.FAILED, 
                                      "TTS service failed", str(e))
            return False
    
    async def _initialize_audio_feedback_service(self) -> bool:
        """Initialize audio feedback service"""
        try:
            from audio_feedback import get_audio_feedback
            
            self.services['audio_feedback'] = get_audio_feedback()
            self._update_service_health('audio_feedback', ServiceStatus.AVAILABLE, 
                                      "Audio feedback service initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio feedback service initialization failed: {e}")
            self._update_service_health('audio_feedback', ServiceStatus.FAILED, 
                                      "Audio feedback service failed", str(e))
            return False
    
    async def _initialize_web_interface_service(self) -> bool:
        """Initialize web interface service"""
        try:
            # Web interface is optional and starts separately
            self._update_service_health('web_interface', ServiceStatus.AVAILABLE, 
                                      "Web interface ready")
            return True
            
        except Exception as e:
            self.logger.error(f"Web interface service initialization failed: {e}")
            self._update_service_health('web_interface', ServiceStatus.FAILED, 
                                      "Web interface failed", str(e))
            return False
    
    async def _initialize_fallback_service(self, service_name: str) -> bool:
        """Initialize fallback service for failed primary service"""
        try:
            if service_name == 'stt':
                return await self._initialize_stt_fallback()
            elif service_name == 'tts':
                return await self._initialize_tts_fallback()
            elif service_name == 'wake_word':
                return await self._initialize_wake_word_fallback()
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Fallback service initialization failed for {service_name}: {e}")
            return False
    
    async def _initialize_stt_fallback(self) -> bool:
        """Initialize STT fallback service"""
        try:
            # Try OpenAI Whisper as fallback
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key:
                self.logger.warning("OpenAI API key not available for STT fallback")
                return False
            
            # Create simple fallback STT service
            self.fallback_services['stt'] = "openai_whisper"
            self._update_service_health('stt', ServiceStatus.DEGRADED, 
                                      "Using OpenAI Whisper fallback", fallback_available=True)
            return True
            
        except Exception as e:
            self.logger.error(f"STT fallback initialization failed: {e}")
            return False
    
    async def _initialize_tts_fallback(self) -> bool:
        """Initialize TTS fallback service"""
        try:
            # Try system TTS as fallback
            self.fallback_services['tts'] = "system_tts"
            self._update_service_health('tts', ServiceStatus.DEGRADED, 
                                      "Using system TTS fallback", fallback_available=True)
            return True
            
        except Exception as e:
            self.logger.error(f"TTS fallback initialization failed: {e}")
            return False
    
    async def _initialize_wake_word_fallback(self) -> bool:
        """Initialize wake word fallback service"""
        try:
            # Use button press as fallback
            self.fallback_services['wake_word'] = "button_press"
            self._update_service_health('wake_word', ServiceStatus.DEGRADED, 
                                      "Using button press fallback", fallback_available=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Wake word fallback initialization failed: {e}")
            return False
    
    def _update_service_health(self, service_name: str, status: ServiceStatus, 
                              message: str, error: Optional[str] = None, 
                              fallback_available: bool = False):
        """Update service health status"""
        import time
        
        self.service_health[service_name] = ServiceHealth(
            status=status,
            message=message,
            last_check=time.time(),
            error=error,
            fallback_available=fallback_available
        )
    
    def _report_service_status(self):
        """Report overall service status"""
        self.logger.info("Service Status Report:")
        self.logger.info("=" * 50)
        
        for service_name, health in self.service_health.items():
            status_emoji = {
                ServiceStatus.AVAILABLE: "✅",
                ServiceStatus.DEGRADED: "⚠️",
                ServiceStatus.UNAVAILABLE: "❌", 
                ServiceStatus.FAILED: "🔥"
            }.get(health.status, "❓")
            
            fallback_info = " (fallback available)" if health.fallback_available else ""
            self.logger.info(f"{status_emoji} {service_name.upper()}: {health.message}{fallback_info}")
            
            if health.error:
                self.logger.debug(f"   Error: {health.error}")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get service instance"""
        return self.services.get(service_name)
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get service health status"""
        return self.service_health.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get all service health statuses"""
        return self.service_health.copy()
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if service is available"""
        health = self.service_health.get(service_name)
        if not health:
            return False
        return health.status in [ServiceStatus.AVAILABLE, ServiceStatus.DEGRADED]
    
    def get_degraded_services(self) -> List[str]:
        """Get list of degraded services"""
        return [
            name for name, health in self.service_health.items() 
            if health.status == ServiceStatus.DEGRADED
        ]
    
    def get_failed_services(self) -> List[str]:
        """Get list of failed services"""
        return [
            name for name, health in self.service_health.items() 
            if health.status == ServiceStatus.FAILED
        ]
    
    def can_operate(self) -> bool:
        """Check if system can operate with current service status"""
        # Minimum required services for basic operation
        required_services = ['wake_word', 'stt', 'llm', 'tts']
        
        available_count = 0
        for service in required_services:
            if self.is_service_available(service):
                available_count += 1
        
        # Can operate if at least 3 out of 4 core services are available
        return available_count >= 3
    
    async def cleanup_services(self):
        """Clean up all services"""
        self.logger.info("Cleaning up services...")
        
        for service_name, service in self.services.items():
            if service and hasattr(service, 'cleanup'):
                try:
                    await service.cleanup()
                    self.logger.info(f"Cleaned up {service_name} service")
                except Exception as e:
                    self.logger.error(f"Error cleaning up {service_name}: {e}")
        
        # Clean up audio feedback
        try:
            from audio_feedback import cleanup_audio_feedback
            cleanup_audio_feedback()
        except Exception as e:
            self.logger.error(f"Error cleaning up audio feedback: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_report = {
            'timestamp': time.time(),
            'overall_status': 'healthy' if self.can_operate() else 'degraded',
            'services': {},
            'system_info': {
                'can_operate': self.can_operate(),
                'degraded_services': self.get_degraded_services(),
                'failed_services': self.get_failed_services()
            }
        }
        
        for service_name, health in self.service_health.items():
            health_report['services'][service_name] = {
                'status': health.status.value,
                'message': health.message,
                'last_check': health.last_check,
                'error': health.error,
                'fallback_available': health.fallback_available
            }
        
        return health_report


async def initialize_services(config_validator: ConfigValidator) -> ServiceManager:
    """Initialize service manager and all services"""
    service_manager = ServiceManager(config_validator)
    
    success = await service_manager.initialize_all_services()
    
    if not success:
        logger.warning("Some services failed to initialize, but continuing with available services")
    
    if not service_manager.can_operate():
        logger.error("Critical: System cannot operate with current service status")
        raise RuntimeError("Insufficient services available for operation")
    
    return service_manager


if __name__ == "__main__":
    # Test service manager
    import asyncio
    import sys
    
    async def test_service_manager():
        from config_validator import validate_configuration
        
        logging.basicConfig(level=logging.INFO)
        
        # Validate configuration
        is_valid, validator = validate_configuration()
        if not is_valid:
            print("Configuration validation failed")
            sys.exit(1)
        
        # Initialize services
        try:
            service_manager = await initialize_services(validator)
            
            # Perform health check
            health_report = await service_manager.health_check()
            
            print("\n" + "="*50)
            print("HEALTH CHECK REPORT")
            print("="*50)
            print(f"Overall Status: {health_report['overall_status'].upper()}")
            print(f"Can Operate: {health_report['system_info']['can_operate']}")
            
            if health_report['system_info']['degraded_services']:
                print(f"Degraded Services: {', '.join(health_report['system_info']['degraded_services'])}")
            
            if health_report['system_info']['failed_services']:
                print(f"Failed Services: {', '.join(health_report['system_info']['failed_services'])}")
            
            # Cleanup
            await service_manager.cleanup_services()
            
        except Exception as e:
            print(f"Service manager test failed: {e}")
            sys.exit(1)
    
    asyncio.run(test_service_manager())