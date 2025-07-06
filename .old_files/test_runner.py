#!/usr/bin/env python3
"""
Comprehensive Test Runner for StorytellerPi
Runs all tests and verifies system integrity
"""

import os
import sys
import subprocess
import logging
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main'))

from config_validator import validate_configuration
from service_manager import initialize_services


class TestRunner:
    """Comprehensive test runner for StorytellerPi"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.test_results = {}
        self.overall_success = True
    
    def _setup_logging(self):
        """Setup logging for test runner"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def run_all_tests(self) -> bool:
        """Run all test suites"""
        self.logger.info("🚀 Starting StorytellerPi Comprehensive Test Suite")
        self.logger.info("=" * 60)
        
        # Test suites to run
        test_suites = [
            ("Environment Setup", self.test_environment_setup),
            ("Configuration Validation", self.test_configuration_validation),
            ("Dependencies Check", self.test_dependencies),
            ("Audio System", self.test_audio_system),
            ("Service Initialization", self.test_service_initialization),
            ("Unit Tests", self.test_unit_tests),
            ("Integration Tests", self.test_integration_tests),
            ("Mock Services", self.test_mock_services),
            ("System Performance", self.test_system_performance),
            ("Security Check", self.test_security)
        ]
        
        for suite_name, test_function in test_suites:
            self.logger.info(f"\n📋 Running {suite_name}...")
            try:
                result = test_function()
                self.test_results[suite_name] = result
                
                if result:
                    self.logger.info(f"✅ {suite_name}: PASSED")
                else:
                    self.logger.error(f"❌ {suite_name}: FAILED")
                    self.overall_success = False
                    
            except Exception as e:
                self.logger.error(f"🔥 {suite_name}: CRITICAL ERROR - {e}")
                self.test_results[suite_name] = False
                self.overall_success = False
        
        # Generate test report
        self._generate_test_report()
        
        return self.overall_success
    
    def test_environment_setup(self) -> bool:
        """Test environment setup"""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or python_version.minor < 9:
                self.logger.error(f"Python 3.9+ required, found {python_version.major}.{python_version.minor}")
                return False
            
            # Check required directories
            required_dirs = ['main', 'tests', 'models', 'credentials']
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    self.logger.error(f"Required directory missing: {dir_name}")
                    return False
            
            # Check .env file exists
            if not os.path.exists('.env'):
                self.logger.warning(".env file not found - using .env.example")
                if not os.path.exists('.env.example'):
                    self.logger.error("No .env or .env.example file found")
                    return False
            
            self.logger.info("Environment setup verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Environment setup test failed: {e}")
            return False
    
    def test_configuration_validation(self) -> bool:
        """Test configuration validation"""
        try:
            # Test with .env.test file if available, otherwise .env
            env_file = '.env.test' if os.path.exists('.env.test') else ('.env' if os.path.exists('.env') else '.env.example')
            is_valid, validator = validate_configuration(env_file)
            
            if not is_valid:
                self.logger.error("Configuration validation failed:")
                for error in validator.get_validation_errors():
                    self.logger.error(f"  - {error}")
                return False
            
            # Check warnings
            if validator.get_warnings():
                self.logger.warning("Configuration warnings:")
                for warning in validator.get_warnings():
                    self.logger.warning(f"  - {warning}")
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation test failed: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test Python dependencies"""
        try:
            # Check requirements.txt
            if not os.path.exists('requirements.txt'):
                self.logger.error("requirements.txt not found")
                return False
            
            # Try importing key dependencies
            required_imports = [
                ('flask', 'Flask web framework'),
                ('numpy', 'NumPy for audio processing'),
                ('pygame', 'Pygame for audio playback'),
                ('psutil', 'System monitoring'),
                ('dotenv', 'Environment variable loading')
            ]
            
            for module_name, description in required_imports:
                try:
                    __import__(module_name)
                    self.logger.debug(f"✓ {description}")
                except ImportError:
                    self.logger.error(f"✗ {description} not available")
                    return False
            
            # Check optional dependencies
            optional_imports = [
                ('google.cloud.speech', 'Google Cloud Speech'),
                ('google.generativeai', 'Google Gemini AI'),
                ('elevenlabs', 'ElevenLabs TTS'),
                ('pvporcupine', 'Porcupine Wake Word'),
                ('openwakeword', 'OpenWakeWord'),
                ('openai', 'OpenAI API')
            ]
            
            available_optional = 0
            for module_name, description in optional_imports:
                try:
                    __import__(module_name)
                    self.logger.debug(f"✓ {description} (optional)")
                    available_optional += 1
                except ImportError:
                    self.logger.debug(f"✗ {description} (optional, not available)")
            
            self.logger.info(f"Dependencies check passed ({available_optional}/{len(optional_imports)} optional dependencies available)")
            return True
            
        except Exception as e:
            self.logger.error(f"Dependencies test failed: {e}")
            return False
    
    def test_audio_system(self) -> bool:
        """Test audio system functionality"""
        try:
            import pyaudio
            
            # Test PyAudio initialization
            audio = pyaudio.PyAudio()
            
            # Check for input devices
            input_devices = []
            output_devices = []
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(device_info)
                if device_info['maxOutputChannels'] > 0:
                    output_devices.append(device_info)
            
            audio.terminate()
            
            if not input_devices:
                self.logger.error("No audio input devices found")
                return False
            
            if not output_devices:
                self.logger.error("No audio output devices found")
                return False
            
            self.logger.info(f"Audio system check passed ({len(input_devices)} input, {len(output_devices)} output devices)")
            return True
            
        except ImportError:
            self.logger.error("PyAudio not available")
            return False
        except Exception as e:
            self.logger.error(f"Audio system test failed: {e}")
            return False
    
    def test_service_initialization(self) -> bool:
        """Test service initialization"""
        try:
            # Test with mock services to avoid API calls
            os.environ['MOCK_SERVICES'] = 'true'
            
            # Validate configuration first
            env_file = '.env.test' if os.path.exists('.env.test') else ('.env' if os.path.exists('.env') else '.env.example')
            is_valid, validator = validate_configuration(env_file)
            
            if not is_valid:
                self.logger.error("Configuration invalid for service test")
                return False
            
            # Test service manager initialization
            async def test_services():
                try:
                    service_manager = await initialize_services(validator)
                    
                    # Check if services are initialized
                    services = ['wake_word', 'stt', 'llm', 'tts', 'audio_feedback']
                    for service_name in services:
                        if not service_manager.is_service_available(service_name):
                            self.logger.warning(f"Service {service_name} not available")
                    
                    # Check if system can operate
                    if not service_manager.can_operate():
                        self.logger.error("System cannot operate with current service status")
                        return False
                    
                    # Cleanup
                    await service_manager.cleanup_services()
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Service initialization failed: {e}")
                    return False
            
            # Run async test
            result = asyncio.run(test_services())
            
            if result:
                self.logger.info("Service initialization test passed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Service initialization test failed: {e}")
            return False
        finally:
            # Clean up mock environment
            if 'MOCK_SERVICES' in os.environ:
                del os.environ['MOCK_SERVICES']
    
    def test_unit_tests(self) -> bool:
        """Run unit tests"""
        try:
            # Run pytest on basic tests
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_basic.py', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Unit tests passed")
                if self.verbose:
                    self.logger.debug(result.stdout)
                return True
            else:
                self.logger.error("Unit tests failed")
                self.logger.error(result.stdout)
                self.logger.error(result.stderr)
                return False
                
        except Exception as e:
            self.logger.error(f"Unit tests execution failed: {e}")
            return False
    
    def test_integration_tests(self) -> bool:
        """Run integration tests"""
        try:
            # Run pytest on integration tests
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Integration tests passed")
                if self.verbose:
                    self.logger.debug(result.stdout)
                return True
            else:
                self.logger.error("Integration tests failed")
                self.logger.error(result.stdout)
                self.logger.error(result.stderr)
                return False
                
        except Exception as e:
            self.logger.error(f"Integration tests execution failed: {e}")
            return False
    
    def test_mock_services(self) -> bool:
        """Test mock services functionality"""
        try:
            # Test mock services
            result = subprocess.run(
                [sys.executable, 'tests/test_mocks.py'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Mock services test passed")
                if self.verbose:
                    self.logger.debug(result.stdout)
                return True
            else:
                self.logger.error("Mock services test failed")
                self.logger.error(result.stdout)
                self.logger.error(result.stderr)
                return False
                
        except Exception as e:
            self.logger.error(f"Mock services test failed: {e}")
            return False
    
    def test_system_performance(self) -> bool:
        """Test system performance"""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"High memory usage: {memory.percent}%")
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"Low disk space: {disk.percent}% used")
            
            self.logger.info(f"System performance: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")
            return True
            
        except Exception as e:
            self.logger.error(f"System performance test failed: {e}")
            return False
    
    def test_security(self) -> bool:
        """Basic security checks"""
        try:
            # Check file permissions
            sensitive_files = ['.env', 'credentials/']
            
            for file_path in sensitive_files:
                if os.path.exists(file_path):
                    stat_info = os.stat(file_path)
                    # Check if readable by others
                    if stat_info.st_mode & 0o044:
                        self.logger.warning(f"File {file_path} is readable by others")
            
            # Check for hardcoded secrets in code
            code_files = list(Path('main').glob('*.py'))
            suspicious_patterns = ['password', 'secret', 'api_key', 'token']
            
            for code_file in code_files:
                try:
                    with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for pattern in suspicious_patterns:
                            if f'{pattern} = ' in content or f'{pattern}=' in content:
                                # Check if it's just a variable assignment without actual secret
                                lines = content.split('\n')
                                for line in lines:
                                    if f'{pattern} = ' in line and not ('os.getenv' in line or 'environ' in line):
                                        self.logger.warning(f"Potential hardcoded secret in {code_file}: {line.strip()}")
                except Exception as e:
                    self.logger.debug(f"Could not read {code_file}: {e}")
            
            self.logger.info("Security check completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Security check failed: {e}")
            return False
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 COMPREHENSIVE TEST REPORT")
        self.logger.info("=" * 60)
        
        # Overall status
        if self.overall_success:
            self.logger.info("🎉 OVERALL STATUS: ALL TESTS PASSED")
        else:
            self.logger.error("❌ OVERALL STATUS: SOME TESTS FAILED")
        
        # Detailed results
        self.logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.logger.info(f"  {status} - {test_name}")
        
        # Statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        self.logger.info(f"\n📈 Statistics:")
        self.logger.info(f"  Total Tests: {total_tests}")
        self.logger.info(f"  Passed: {passed_tests}")
        self.logger.info(f"  Failed: {failed_tests}")
        self.logger.info(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Recommendations
        if failed_tests > 0:
            self.logger.info(f"\n💡 Recommendations:")
            self.logger.info("  1. Check failed test details above")
            self.logger.info("  2. Verify configuration in .env file")
            self.logger.info("  3. Ensure all dependencies are installed")
            self.logger.info("  4. Check system requirements")
            self.logger.info("  5. Review setup guide: SETUP_GUIDE.md")
        else:
            self.logger.info(f"\n🚀 System is ready for production!")
            self.logger.info("  You can now start the StorytellerPi service")
        
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="StorytellerPi Test Runner")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quick', '-q', action='store_true', help='Run quick tests only')
    
    args = parser.parse_args()
    
    # Create test runner
    test_runner = TestRunner(verbose=args.verbose)
    
    # Run tests
    success = test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()